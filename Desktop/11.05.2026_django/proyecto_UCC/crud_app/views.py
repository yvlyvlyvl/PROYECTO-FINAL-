from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import date
from .models import Habitacion, Reserva, Pago, Servicio, Notificacion, Favorito, CodigoVerificacion, Calificacion, FotoHabitacion
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
import json

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# ── Página principal ──
def pagina_principal(request):
    return render(request, 'crud_app/index.html')


# ── Dashboard usuario ──
@login_required(login_url='login')
def home(request):
    reservas    = Reserva.objects.filter(usuario=request.user).order_by('-fecha_reserva')[:5]
    notif_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    proxima     = Reserva.objects.filter(
        usuario=request.user,
        estado__in=['confirmada', 'pendiente']
    ).order_by('check_in').first()

    return render(request, 'crud_app/home.html', {
        'reservas'    : reservas,
        'notif_count' : notif_count,
        'proxima'     : proxima,
    })


# ── Dashboard admin ──
@login_required(login_url='login')
def home_admin(request):
    total_habitaciones = Habitacion.objects.count()
    disponibles        = Habitacion.objects.filter(estado='disponible').count()
    ocupadas           = Habitacion.objects.filter(estado='ocupada').count()
    reservas_hoy       = Reserva.objects.filter(check_in=date.today()).count()
    reservas_recientes = Reserva.objects.all().order_by('-fecha_reserva')[:5]
    servicios_hoy      = Servicio.objects.filter(fecha_solicitud__date=date.today())

    return render(request, 'crud_app/home_admin.html', {
        'total_habitaciones' : total_habitaciones,
        'disponibles'        : disponibles,
        'ocupadas'           : ocupadas,
        'reservas_hoy'       : reservas_hoy,
        'reservas_recientes' : reservas_recientes,
        'servicios_hoy'      : servicios_hoy,
    })


# ── Login ──
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        tipo     = request.POST.get('tipo', 'usuario')
        user     = authenticate(request, username=username, password=password)
        if user is not None:
            if tipo == 'admin' and not user.is_staff:
                messages.error(request, 'No tienes permisos de administrador')
                return redirect('login')
            login(request, user)
            messages.success(request, f'Bienvenido {username}')
            return redirect('home_admin') if tipo == 'admin' else redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
            return redirect('login')
    return render(request, 'crud_app/login.html')


# ── Logout ──
def logout_user(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente')
    return redirect('pagina_principal')


# ── Register ──
def register_user(request):
    if request.method == 'POST':
        username  = request.POST['username']
        email     = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('register')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return redirect('register')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo ya está en uso')
            return redirect('register')

        User.objects.create_user(username=username, email=email, password=password1)
        messages.success(request, 'Cuenta creada con éxito. Ahora puedes iniciar sesión')
        return redirect('login')

    return render(request, 'crud_app/register.html')


# ── Perfil ──
@login_required(login_url='login')
def perfil_usuario(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        if email and email != request.user.email:
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Ese correo ya está en uso')
                return redirect('perfil_usuario')
            request.user.email = email
            request.user.save()
            messages.success(request, 'Correo actualizado correctamente')
        else:
            messages.info(request, 'No se realizaron cambios')
        return redirect('perfil_usuario')
    return render(request, 'crud_app/perfil_usuario.html')


# ── Cambiar contraseña ──
@login_required(login_url='login')
def cambiar_contrasena(request):
    if request.method == 'POST':
        actual    = request.POST.get('contrasena_actual')
        nueva     = request.POST.get('contrasena_nueva')
        confirmar = request.POST.get('contrasena_confirmar')

        if not request.user.check_password(actual):
            messages.error(request, 'La contraseña actual es incorrecta')
            return redirect('cambiar_contrasena')
        if nueva != confirmar:
            messages.error(request, 'Las contraseñas nuevas no coinciden')
            return redirect('cambiar_contrasena')
        if len(nueva) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return redirect('cambiar_contrasena')

        request.user.set_password(nueva)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Contraseña cambiada correctamente')
        return redirect('perfil_usuario')

    return render(request, 'crud_app/cambiar_contrasena.html')


# ── Recuperar cuenta ──
def recuperar_cuenta(request):
    if request.method == 'POST':
        correo = request.POST.get('correo', '')
        try:
            user = User.objects.get(email=correo)
        except User.DoesNotExist:
            messages.error(request, 'No existe una cuenta con ese correo')
            return redirect('recuperar_cuenta')

        codigo = CodigoVerificacion.generar_codigo()
        CodigoVerificacion.objects.create(user=user, codigo=codigo)

        send_mail(
            subject        = 'Código de verificación — Hotel Casa Marco',
            message        = f'Hola {user.username},\n\nTu código es: {codigo}\n\nSi no lo solicitaste, ignora este mensaje.',
            from_email     = 'vergarajoey60@gmail.com',
            recipient_list = [correo],
            fail_silently  = False,
        )

        messages.success(request, f'Código enviado a {correo}')
        request.session['correo_recuperacion'] = correo
        return redirect('verificar_codigo')

    return render(request, 'crud_app/recuperar_cuenta.html')


def verificar_codigo(request):
    correo = request.session.get('correo_recuperacion', '')
    if not correo:
        return redirect('recuperar_cuenta')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '')
        try:
            user   = User.objects.get(email=correo)
            codigo = CodigoVerificacion.objects.filter(
                user=user, codigo=codigo_ingresado, usado=False
            ).last()
            if codigo:
                codigo.usado = True
                codigo.save()
                request.session['codigo_verificado'] = True
                return redirect('nueva_contrasena')
            else:
                messages.error(request, 'Código incorrecto o ya usado')
                return redirect('verificar_codigo')
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
            return redirect('recuperar_cuenta')

    return render(request, 'crud_app/verificar_codigo.html', {'correo': correo})


def nueva_contrasena(request):
    correo            = request.session.get('correo_recuperacion', '')
    codigo_verificado = request.session.get('codigo_verificado', False)

    if not correo or not codigo_verificado:
        return redirect('recuperar_cuenta')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('nueva_contrasena')
        if len(password1) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return redirect('nueva_contrasena')

        user = User.objects.get(email=correo)
        user.set_password(password1)
        user.save()

        del request.session['correo_recuperacion']
        del request.session['codigo_verificado']

        messages.success(request, 'Contraseña cambiada correctamente')
        return redirect('login')

    return render(request, 'crud_app/nueva_contrasena.html')


# ── Habitaciones usuario ──
@login_required(login_url='login')
def reservar_habitacion(request):
    tipo         = request.GET.get('tipo', '')
    habitaciones = Habitacion.objects.all().order_by('numero')
    if tipo:
        habitaciones = habitaciones.filter(tipo=tipo)
    return render(request, 'crud_app/reservar_habitacion.html', {
        'habitaciones': habitaciones,
        'tipo'        : tipo,
    })


@login_required(login_url='login')
def confirmar_reserva(request, hab_pk):
    habitacion = Habitacion.objects.get(pk=hab_pk)

    if request.method == 'POST':
        check_in       = request.POST.get('check_in')
        check_out      = request.POST.get('check_out')
        adultos        = int(request.POST.get('adultos', 1))
        ninos          = int(request.POST.get('ninos', 0))
        nombre_huesped = request.POST.get('nombre_huesped')
        documento      = request.POST.get('documento')
        telefono       = request.POST.get('telefono')
        solicitudes    = request.POST.get('solicitudes', '')

        from datetime import datetime
        ci     = datetime.strptime(check_in,  '%Y-%m-%d').date()
        co     = datetime.strptime(check_out, '%Y-%m-%d').date()
        noches = (co - ci).days

        if noches <= 0:
            messages.error(request, 'La fecha de salida debe ser posterior a la de entrada')
            return redirect('confirmar_reserva', hab_pk=hab_pk)

        total  = habitacion.precio_noche * noches
        codigo = Reserva.generar_codigo()

        reserva = Reserva.objects.create(
            usuario        = request.user,
            habitacion     = habitacion,
            codigo         = codigo,
            check_in       = ci,
            check_out      = co,
            adultos        = adultos,
            ninos          = ninos,
            huespedes      = adultos + ninos,
            total          = total,
            nombre_huesped = nombre_huesped,
            documento      = documento,
            telefono       = telefono,
            solicitudes    = solicitudes,
            estado         = 'pendiente',
        )

        

        Notificacion.objects.create(
            usuario = request.user,
            tipo    = 'reserva',
            titulo  = f'Reserva {codigo} confirmada ✅',
            mensaje = f'Tu reserva para la habitación {habitacion.numero} del {ci} al {co} ha sido confirmada.',
        )

        messages.success(request, f'Reserva {codigo} realizada correctamente')
        return redirect('mis_reservas')

    return render(request, 'crud_app/confirmar_reserva.html', {'habitacion': habitacion})


# ── Enviar correo reserva ──
@login_required(login_url='login')
def enviar_correo_reserva(request, pk):
    reserva = Reserva.objects.get(pk=pk, usuario=request.user)

    if not request.user.email:
        messages.error(request, 'No tienes un correo registrado en tu perfil.')
        return redirect('mis_reservas')

    try:
        send_mail(
            f'Detalles de Reserva {reserva.codigo} - Hotel Casa Marco',
            f"""
Hola {request.user.username},

Aquí están los detalles de tu reserva en Hotel Casa Marco.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETALLES DE TU RESERVA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Codigo:       {reserva.codigo}
Habitacion:   {reserva.habitacion.numero} - {reserva.habitacion.get_tipo_display()}
Huesped:      {reserva.nombre_huesped}
Check-in:     {reserva.check_in.strftime('%d/%m/%Y')}
Check-out:    {reserva.check_out.strftime('%d/%m/%Y')}
Noches:       {reserva.noches}
Huespedes:    {reserva.huespedes}
Total:        ${reserva.total:,.0f} COP
Estado:       {reserva.get_estado_display()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Puedes gestionar tu reserva en:
http://127.0.0.1:8000/mis-reservas/

Si tienes alguna duda contactanos:
Email: reservas@hotelcasamarco.com
Tel:   +57 312 456 7890

Gracias por elegir Hotel Casa Marco!
El equipo de reservas
            """,
            'Hotel Casa Marco <vergarajoey60@gmail.com>',
            [request.user.email],
            fail_silently=False,
        )
        messages.success(request, f'Correo enviado a {request.user.email} correctamente')
    except Exception:
        messages.error(request, 'No se pudo enviar el correo. Intenta de nuevo.')

    return redirect('mis_reservas')


# ── Mis reservas ──
@login_required(login_url='login')
def mis_reservas(request):
    reservas = Reserva.objects.filter(
        usuario=request.user,
        estado__in=['pendiente', 'confirmada', 'en_curso']
    ).order_by('-fecha_reserva')
    return render(request, 'crud_app/mis_reservas.html', {'reservas': reservas})


@login_required(login_url='login')
def cancelar_reserva(request, pk):
    reserva = Reserva.objects.get(pk=pk, usuario=request.user)
    reserva.estado = 'cancelada'
    reserva.save()

    reserva.habitacion.estado = 'disponible'
    reserva.habitacion.save()

    # Cancelar el pago automáticamente si existe
    try:
        if hasattr(reserva, 'pago') and reserva.pago.estado in ['pendiente', 'confirmado']:
            reserva.pago.estado = 'rechazado'
            reserva.pago.save()
    except:
        pass

    Notificacion.objects.create(
        usuario = request.user,
        tipo    = 'alerta',
        titulo  = f'Reserva {reserva.codigo} cancelada',
        mensaje = f'Tu reserva para la habitación {reserva.habitacion.numero} ha sido cancelada.',
    )

    if request.user.email:
        try:
            send_mail(
                f'Reserva {reserva.codigo} Cancelada - Hotel Casa Marco',
                f"""
Hola {request.user.username},

Tu reserva ha sido cancelada exitosamente.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETALLES DE LA RESERVA CANCELADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Codigo:       {reserva.codigo}
Habitacion:   {reserva.habitacion.numero} - {reserva.habitacion.get_tipo_display()}
Huesped:      {reserva.nombre_huesped}
Check-in:     {reserva.check_in.strftime('%d/%m/%Y')}
Check-out:    {reserva.check_out.strftime('%d/%m/%Y')}
Noches:       {reserva.noches}
Total:        ${reserva.total:,.0f} COP
Estado:       Cancelada
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Si tienes alguna duda contactanos:
Email: reservas@hotelcasamarco.com
Tel:   +57 312 456 7890

Gracias por elegir Hotel Casa Marco.
El equipo de reservas
                """,
                'Hotel Casa Marco <vergarajoey60@gmail.com>',
                [request.user.email],
                fail_silently=True,
            )
        except:
            pass

    messages.success(request, f'Reserva {reserva.codigo} cancelada correctamente')
    return redirect('mis_reservas')


# ── Historial ──
@login_required(login_url='login')
def historial_estadias(request):
    reservas = Reserva.objects.filter(
        usuario=request.user,
        estado__in=['completada', 'cancelada']
    ).order_by('-fecha_reserva')
    return render(request, 'crud_app/historial_estadias.html', {'reservas': reservas})


# ── Pagos ──
@login_required(login_url='login')
def mis_pagos(request):
    pagos = Pago.objects.filter(usuario=request.user).order_by('-fecha_pago')
    return render(request, 'crud_app/mis_pagos.html', {'pagos': pagos})


@login_required(login_url='login')
def realizar_pago(request, reserva_pk):
    reserva = Reserva.objects.get(pk=reserva_pk, usuario=request.user)

    if hasattr(reserva, 'pago') and reserva.pago.estado != 'rechazado':
        messages.info(request, 'Esta reserva ya tiene un pago registrado')
        return redirect('mis_pagos')

    if request.method == 'POST':
        metodo         = request.POST.get('metodo')
        nombre_titular = request.POST.get('nombre_titular', '')
        numero_tarjeta = request.POST.get('numero_tarjeta', '')
        banco          = request.POST.get('banco', '')

        if numero_tarjeta:
            numero_tarjeta = numero_tarjeta[-4:]

        referencia = Pago.generar_referencia()

        Pago.objects.create(
            reserva        = reserva,
            usuario        = request.user,
            metodo         = metodo,
            total          = reserva.total,
            referencia     = referencia,
            nombre_titular = nombre_titular,
            numero_tarjeta = numero_tarjeta,
            banco          = banco,
            estado         = 'confirmado',
        )

        Notificacion.objects.create(
            usuario = request.user,
            tipo    = 'pago',
            titulo  = 'Pago recibido correctamente ✅',
            mensaje = f'Tu pago de ${reserva.total} para la reserva {reserva.codigo} fue procesado.',
        )

        messages.success(request, f'Pago {referencia} realizado correctamente')
        return redirect('mis_pagos')

    return render(request, 'crud_app/realizar_pago.html', {'reserva': reserva})


@login_required(login_url='login')
def cancelar_pago(request, pk):
    pago = Pago.objects.get(pk=pk, usuario=request.user)
    if pago.estado in ['pendiente', 'confirmado']:
        pago.estado = 'rechazado'
        pago.save()
        Notificacion.objects.create(
            usuario = request.user,
            tipo    = 'alerta',
            titulo  = f'Pago {pago.referencia} cancelado',
            mensaje = f'Tu pago para la reserva {pago.reserva.codigo} ha sido cancelado.',
        )
        messages.success(request, f'Pago {pago.referencia} cancelado correctamente')
    else:
        messages.error(request, 'Este pago no puede ser cancelado')
    return redirect('mis_pagos')


# ── Notificaciones ──
@login_required(login_url='login')
def notificaciones(request):
    notifs = Notificacion.objects.filter(usuario=request.user).order_by('-creado_el')
    notifs.filter(leida=False).update(leida=True)
    return render(request, 'crud_app/notificaciones.html', {'notificaciones': notifs})


# ── Favoritos ──
@login_required(login_url='login')
def favoritos(request):
    favs = Favorito.objects.filter(usuario=request.user).select_related('habitacion')
    return render(request, 'crud_app/favoritos.html', {'favoritos': favs})


@login_required(login_url='login')
def toggle_favorito(request, hab_pk):
    habitacion  = Habitacion.objects.get(pk=hab_pk)
    fav, creado = Favorito.objects.get_or_create(usuario=request.user, habitacion=habitacion)
    if not creado:
        fav.delete()
        messages.info(request, f'"{habitacion.numero}" eliminado de favoritos')
    else:
        messages.success(request, f'"{habitacion.numero}" agregado a favoritos')
    return redirect('reservar_habitacion')


# ── Servicios ──
@login_required(login_url='login')
def solicitar_servicio(request, reserva_pk):
    reserva = Reserva.objects.get(pk=reserva_pk, usuario=request.user)

    if request.method == 'POST':
        tipo        = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion', '')
        costo       = request.POST.get('costo', 0)

        Servicio.objects.create(
            reserva     = reserva,
            tipo        = tipo,
            descripcion = descripcion,
            costo       = costo,
        )

        Notificacion.objects.create(
            usuario = request.user,
            tipo    = 'info',
            titulo  = 'Servicio solicitado ✅',
            mensaje = f'Tu solicitud de {tipo} para la reserva {reserva.codigo} fue registrada.',
        )

        messages.success(request, 'Servicio solicitado correctamente')
        return redirect('mis_reservas')

    return render(request, 'crud_app/solicitar_servicio.html', {'reserva': reserva})


# ── Calificaciones ──
@login_required(login_url='login')
def calificar_estadia(request, reserva_pk):
    reserva = Reserva.objects.get(pk=reserva_pk, usuario=request.user)

    if hasattr(reserva, 'calificacion'):
        messages.info(request, 'Ya calificaste esta estadía')
        return redirect('historial_estadias')

    if reserva.estado not in ['completada', 'cancelada']:
        messages.error(request, 'Solo puedes calificar estadías completadas')
        return redirect('historial_estadias')

    if request.method == 'POST':
        estrellas  = int(request.POST.get('estrellas', 5))
        comentario = request.POST.get('comentario', '')

        Calificacion.objects.create(
            usuario    = request.user,
            reserva    = reserva,
            habitacion = reserva.habitacion,
            estrellas  = estrellas,
            comentario = comentario,
        )

        Notificacion.objects.create(
            usuario = request.user,
            tipo    = 'info',
            titulo  = '¡Gracias por tu calificación! ⭐',
            mensaje = f'Calificaste tu estadía en la habitación {reserva.habitacion.numero} con {estrellas} estrellas.',
        )

        messages.success(request, '¡Gracias por tu calificación!')
        return redirect('historial_estadias')

    return render(request, 'crud_app/calificar_estadia.html', {'reserva': reserva})


@login_required(login_url='login')
def mis_calificaciones(request):
    calificaciones = Calificacion.objects.filter(usuario=request.user).order_by('-creado_el')
    return render(request, 'crud_app/mis_calificaciones.html', {'calificaciones': calificaciones})


# ── Contacto ──
@login_required(login_url='login')
def contacto(request):
    if request.method == 'POST':
        nombre  = request.POST.get('nombre')
        correo  = request.POST.get('correo')
        asunto  = request.POST.get('asunto')
        mensaje = request.POST.get('mensaje')

        send_mail(
            subject        = f'Contacto Hotel Casa Marco — {asunto}',
            message        = f'De: {nombre} ({correo})\n\nMensaje:\n{mensaje}',
            from_email     = 'vergarajoey60@gmail.com',
            recipient_list = ['vergarajoey60@gmail.com'],
            fail_silently  = False,
        )

        messages.success(request, 'Mensaje enviado correctamente.')
        return redirect('contacto')

    return render(request, 'crud_app/contacto.html')


# ── Admin: Habitaciones ──
@login_required(login_url='login')
def admin_habitaciones(request):
    if not request.user.is_staff:
        return redirect('home')
    habitaciones = Habitacion.objects.all().order_by('numero')
    return render(request, 'crud_app/admin_habitaciones.html', {'habitaciones': habitaciones})


@login_required(login_url='login')
def admin_crear_habitacion(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        habitacion = Habitacion.objects.create(
            numero       = request.POST.get('numero'),
            tipo         = request.POST.get('tipo'),
            descripcion  = request.POST.get('descripcion'),
            precio_noche = request.POST.get('precio_noche'),
            capacidad    = request.POST.get('capacidad'),
            piso         = request.POST.get('piso'),
            amenidades   = request.POST.get('amenidades', ''),
            imagen       = request.FILES.get('imagen'),
        )
        fotos = request.FILES.getlist('fotos_galeria')
        for i, foto in enumerate(fotos):
            FotoHabitacion.objects.create(
                habitacion = habitacion,
                imagen     = foto,
                orden      = i
            )
        messages.success(request, f'Habitación {habitacion.numero} creada correctamente')
        return redirect('admin_habitaciones')

    return render(request, 'crud_app/admin_crear_habitacion.html')


@login_required(login_url='login')
def admin_editar_habitacion(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    habitacion = Habitacion.objects.get(pk=pk)

    if request.method == 'POST':
        habitacion.numero       = request.POST.get('numero')
        habitacion.tipo         = request.POST.get('tipo')
        habitacion.descripcion  = request.POST.get('descripcion')
        habitacion.precio_noche = request.POST.get('precio_noche')
        habitacion.capacidad    = request.POST.get('capacidad')
        habitacion.piso         = request.POST.get('piso')
        habitacion.estado       = request.POST.get('estado')
        habitacion.amenidades   = request.POST.get('amenidades', '')

        if request.FILES.get('imagen'):
            habitacion.imagen = request.FILES.get('imagen')

        habitacion.save()
        messages.success(request, 'Habitación actualizada correctamente')
        return redirect('admin_habitaciones')

    return render(request, 'crud_app/admin_editar_habitacion.html', {'habitacion': habitacion})


@login_required(login_url='login')
def admin_eliminar_habitacion(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    habitacion = Habitacion.objects.get(pk=pk)
    habitacion.delete()
    messages.success(request, 'Habitación eliminada correctamente')
    return redirect('admin_habitaciones')


# ── Admin: Fotos ──
@login_required(login_url='login')
def admin_fotos_habitacion(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    habitacion = Habitacion.objects.get(pk=pk)

    if request.method == 'POST':
        fotos = request.FILES.getlist('fotos')
        for i, foto in enumerate(fotos):
            FotoHabitacion.objects.create(
                habitacion = habitacion,
                imagen     = foto,
                orden      = habitacion.fotos.count() + i
            )
        messages.success(request, f'{len(fotos)} foto(s) agregada(s) correctamente')
        return redirect('admin_fotos_habitacion', pk=pk)

    fotos = habitacion.fotos.all()
    return render(request, 'crud_app/admin_fotos_habitacion.html', {
        'habitacion': habitacion,
        'fotos'     : fotos,
    })


@login_required(login_url='login')
def admin_eliminar_foto(request, foto_pk):
    if not request.user.is_staff:
        return redirect('home')
    foto   = FotoHabitacion.objects.get(pk=foto_pk)
    hab_pk = foto.habitacion.pk
    foto.imagen.delete()
    foto.delete()
    messages.success(request, 'Foto eliminada correctamente')
    return redirect('admin_fotos_habitacion', pk=hab_pk)


# ── Admin: Reservas ──
@login_required(login_url='login')
def admin_reservas(request):
    if not request.user.is_staff:
        return redirect('home')
    reservas = Reserva.objects.all().order_by('-fecha_reserva')
    return render(request, 'crud_app/admin_reservas.html', {'reservas': reservas})


@login_required(login_url='login')
def admin_cambiar_estado_reserva(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    reserva = Reserva.objects.get(pk=pk)
    if request.method == 'POST':
        estado_anterior = reserva.estado
        nuevo_estado    = request.POST.get('estado')
        reserva.estado  = nuevo_estado
        reserva.save()

        # Actualizar estado de habitación según el estado de la reserva
        if nuevo_estado == 'en_curso':
            reserva.habitacion.estado = 'ocupada'
            reserva.habitacion.save()
        elif nuevo_estado in ['completada', 'cancelada']:
            reserva.habitacion.estado = 'disponible'
            reserva.habitacion.save()
        elif nuevo_estado == 'confirmada':
            reserva.habitacion.estado = 'reservada'
            reserva.habitacion.save()

        # Notificar al usuario
        mensajes = {
            'confirmada' : 'Tu reserva ha sido confirmada por el hotel ✅',
            'en_curso'   : 'Tu check-in ha sido registrado. ¡Bienvenido al hotel! 🏨',
            'completada' : 'Tu estadía ha finalizado. ¡Esperamos verte pronto! 🌟',
            'cancelada'  : 'Tu reserva ha sido cancelada por el hotel ❌',
        }

        if nuevo_estado in mensajes:
            Notificacion.objects.create(
                usuario = reserva.usuario,
                tipo    = 'info',
                titulo  = f'Reserva {reserva.codigo} — {reserva.get_estado_display()}',
                mensaje = mensajes[nuevo_estado],
            )

            # Enviar correo al usuario
            if reserva.usuario.email:
                try:
                    send_mail(
                        f'Reserva {reserva.codigo} — {reserva.get_estado_display()} - Hotel Casa Marco',
                        f"""
Hola {reserva.usuario.username},

{mensajes[nuevo_estado]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETALLES DE TU RESERVA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Codigo:       {reserva.codigo}
Habitacion:   {reserva.habitacion.numero} - {reserva.habitacion.get_tipo_display()}
Huesped:      {reserva.nombre_huesped}
Check-in:     {reserva.check_in.strftime('%d/%m/%Y')}
Check-out:    {reserva.check_out.strftime('%d/%m/%Y')}
Noches:       {reserva.noches}
Total:        ${reserva.total:,.0f} COP
Estado:       {reserva.get_estado_display()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Si tienes alguna duda contactanos:
Email: reservas@hotelcasamarco.com
Tel:   +57 312 456 7890

Gracias por elegir Hotel Casa Marco.
El equipo de reservas
                        """,
                        'Hotel Casa Marco <vergarajoey60@gmail.com>',
                        [reserva.usuario.email],
                        fail_silently=True,
                    )
                except:
                    pass

        messages.success(request, f'Estado de reserva {reserva.codigo} actualizado a {reserva.get_estado_display()}')
        return redirect('admin_reservas')

    return render(request, 'crud_app/admin_cambiar_estado_reserva.html', {'reserva': reserva})


# ── Admin: Clientes ──
@login_required(login_url='login')
def admin_clientes(request):
    if not request.user.is_staff:
        return redirect('home')
    clientes = User.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'crud_app/admin_clientes.html', {'clientes': clientes})


# ── Admin: Pagos ──
@login_required(login_url='login')
def admin_pagos(request):
    if not request.user.is_staff:
        return redirect('home')
    pagos          = Pago.objects.all().order_by('-fecha_pago')
    total_ingresos = sum(p.total for p in pagos.filter(estado='confirmado'))
    return render(request, 'crud_app/admin_pagos.html', {
        'pagos'         : pagos,
        'total_ingresos': total_ingresos,
    })


# ── Admin: Servicios ──
@login_required(login_url='login')
def admin_servicios(request):
    if not request.user.is_staff:
        return redirect('home')
    servicios = Servicio.objects.all().order_by('-fecha_solicitud')
    return render(request, 'crud_app/admin_servicios.html', {'servicios': servicios})


@login_required(login_url='login')
def admin_cambiar_estado_servicio(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    servicio = Servicio.objects.get(pk=pk)
    if request.method == 'POST':
        servicio.estado = request.POST.get('estado')
        servicio.save()
        messages.success(request, 'Estado del servicio actualizado')
        return redirect('admin_servicios')
    return render(request, 'crud_app/admin_cambiar_estado_servicio.html', {'servicio': servicio})


# ── Admin: Reportes ──
@login_required(login_url='login')
def admin_reportes(request):
    if not request.user.is_staff:
        return redirect('home')

    total_reservas    = Reserva.objects.count()
    reservas_activas  = Reserva.objects.filter(estado__in=['confirmada', 'en_curso']).count()
    total_ingresos    = Pago.objects.filter(estado='confirmado').aggregate(Sum('total'))['total__sum'] or 0
    total_clientes    = User.objects.filter(is_staff=False).count()
    habitaciones_disp = Habitacion.objects.filter(estado='disponible').count()
    habitaciones_ocup = Habitacion.objects.filter(estado='ocupada').count()

    reservas_mes = Reserva.objects.annotate(
        mes=TruncMonth('fecha_reserva')
    ).values('mes').annotate(total=Count('id')).order_by('mes')[:6]

    meses_labels = [r['mes'].strftime('%b %Y') for r in reservas_mes]
    meses_data   = [r['total'] for r in reservas_mes]

    estados_data = {
        'Pendiente'  : Reserva.objects.filter(estado='pendiente').count(),
        'Confirmada' : Reserva.objects.filter(estado='confirmada').count(),
        'En curso'   : Reserva.objects.filter(estado='en_curso').count(),
        'Completada' : Reserva.objects.filter(estado='completada').count(),
        'Cancelada'  : Reserva.objects.filter(estado='cancelada').count(),
    }

    tipos_data = {}
    for hab in Habitacion.objects.values('tipo').annotate(total=Count('id')):
        tipos_data[hab['tipo']] = hab['total']

    servicios_data = {}
    for s in Servicio.objects.values('tipo').annotate(total=Count('id')):
        servicios_data[s['tipo']] = s['total']

    return render(request, 'crud_app/admin_reportes.html', {
        'total_reservas'    : total_reservas,
        'reservas_activas'  : reservas_activas,
        'total_ingresos'    : total_ingresos,
        'total_clientes'    : total_clientes,
        'habitaciones_disp' : habitaciones_disp,
        'habitaciones_ocup' : habitaciones_ocup,
        'meses_labels'      : json.dumps(meses_labels),
        'meses_data'        : json.dumps(meses_data),
        'estados_labels'    : json.dumps(list(estados_data.keys())),
        'estados_data'      : json.dumps(list(estados_data.values())),
        'tipos_labels'      : json.dumps(list(tipos_data.keys())),
        'tipos_data'        : json.dumps(list(tipos_data.values())),
        'servicios_labels'  : json.dumps(list(servicios_data.keys())),
        'servicios_data'    : json.dumps(list(servicios_data.values())),
    })


# ── Factura PDF ──
@login_required(login_url='login')
def descargar_factura(request, reserva_pk):
    reserva = Reserva.objects.get(pk=reserva_pk, usuario=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Factura_{reserva.codigo}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    naranja    = colors.HexColor('#E8920A')
    azul       = colors.HexColor('#0D1B2A')
    gris       = colors.HexColor('#888888')
    gris_claro = colors.HexColor('#f8f9fa')
    borde      = colors.HexColor('#e5e7eb')

    estilo_normal = ParagraphStyle('normal', fontSize=10, textColor=azul, fontName='Helvetica', spaceAfter=4)
    estilo_bold   = ParagraphStyle('bold',   fontSize=10, textColor=azul, fontName='Helvetica-Bold', spaceAfter=4)
    estilo_centro = ParagraphStyle('centro', fontSize=10, textColor=gris, fontName='Helvetica', alignment=TA_CENTER)

    elementos = []

    # Encabezado
    encabezado_data = [[
        Paragraph('<b>Hotel Casa Marco</b>', ParagraphStyle(
            'logo', fontSize=22, textColor=azul, fontName='Helvetica-Bold', leading=26
        )),
        Paragraph(
            'NIT: 900.123.456-7<br/>Ciénaga de Oro, Córdoba — Colombia<br/>'
            'reservas@hotelcasamarco.com<br/>+57 312 456 7890',
            ParagraphStyle('info_hotel', fontSize=9, textColor=gris,
                           fontName='Helvetica', alignment=TA_RIGHT, leading=14)
        )
    ]]
    tabla_enc = Table(encabezado_data, colWidths=[9*cm, 8*cm])
    tabla_enc.setStyle(TableStyle([
        ('VALIGN',    (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING',   (0,0), (-1,-1), 0),
        ('LINEBELOW', (0,0), (-1,0),  2.5, naranja),
    ]))
    elementos.append(tabla_enc)
    elementos.append(Spacer(1, 0.5*cm))

    # Título y código
    factura_data = [[
        Paragraph('FACTURA DE RESERVA', ParagraphStyle(
            'fact', fontSize=16, textColor=naranja, fontName='Helvetica-Bold'
        )),
        Paragraph(
            f'Código: <b>{reserva.codigo}</b><br/>'
            f'Fecha emisión: {reserva.fecha_reserva.strftime("%d/%m/%Y %H:%M")}',
            ParagraphStyle('cod', fontSize=10, textColor=azul,
                           fontName='Helvetica', alignment=TA_RIGHT, leading=16)
        )
    ]]
    tabla_fac = Table(factura_data, colWidths=[9*cm, 8*cm])
    tabla_fac.setStyle(TableStyle([
        ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    elementos.append(tabla_fac)
    elementos.append(Spacer(1, 0.5*cm))

    # Datos cliente y reserva
    datos_tabla = [
        ['DATOS DEL CLIENTE', '', 'DATOS DE LA RESERVA', ''],
        ['Nombre:',    reserva.nombre_huesped,       'Check-in:',  reserva.check_in.strftime('%d/%m/%Y')],
        ['Usuario:',   reserva.usuario.username,     'Check-out:', reserva.check_out.strftime('%d/%m/%Y')],
        ['Documento:', reserva.documento,            'Noches:',    str(reserva.noches)],
        ['Teléfono:',  reserva.telefono,             'Huéspedes:', str(reserva.huespedes)],
        ['Correo:',    reserva.usuario.email or '—', 'Estado:',    reserva.get_estado_display()],
    ]
    tabla_datos = Table(datos_tabla, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 4.5*cm])
    tabla_datos.setStyle(TableStyle([
        ('FONTNAME',       (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0,0), (-1,0),  9),
        ('TEXTCOLOR',      (0,0), (-1,0),  colors.white),
        ('BACKGROUND',     (0,0), (1,0),   azul),
        ('BACKGROUND',     (2,0), (3,0),   azul),
        ('SPAN',           (0,0), (1,0)),
        ('SPAN',           (2,0), (3,0)),
        ('ALIGN',          (0,0), (-1,0),  'CENTER'),
        ('FONTNAME',       (0,1), (0,-1),  'Helvetica-Bold'),
        ('FONTNAME',       (2,1), (2,-1),  'Helvetica-Bold'),
        ('FONTNAME',       (1,1), (1,-1),  'Helvetica'),
        ('FONTNAME',       (3,1), (3,-1),  'Helvetica'),
        ('FONTSIZE',       (0,1), (-1,-1), 9),
        ('TEXTCOLOR',      (0,1), (-1,-1), azul),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, gris_claro]),
        ('PADDING',        (0,0), (-1,-1), 7),
        ('GRID',           (0,0), (-1,-1), 0.5, borde),
    ]))
    elementos.append(tabla_datos)
    elementos.append(Spacer(1, 0.5*cm))

    # Detalle habitación
    det_header = Table([[Paragraph('DETALLE DE LA ESTADÍA', ParagraphStyle(
        'sec', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER
    ))]], colWidths=[17*cm])
    det_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), azul),
        ('PADDING',    (0,0), (-1,-1), 7),
    ]))
    elementos.append(det_header)

    detalle_tabla = [
        ['Descripción', 'Precio/noche', 'Noches', 'Subtotal'],
        [
            Paragraph(
                f'<b>Habitación {reserva.habitacion.numero} — {reserva.habitacion.get_tipo_display()}</b><br/>'
                f'Piso {reserva.habitacion.piso} · Capacidad: {reserva.habitacion.capacidad} personas',
                ParagraphStyle('desc', fontSize=9, textColor=azul, fontName='Helvetica', leading=13)
            ),
            f'${reserva.habitacion.precio_noche:,.0f}',
            str(reserva.noches),
            f'${reserva.total:,.0f}',
        ],
    ]
    tabla_det = Table(detalle_tabla, colWidths=[8.5*cm, 3*cm, 2*cm, 3.5*cm])
    tabla_det.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,0),  9),
        ('TEXTCOLOR', (0,0), (-1,0),  colors.white),
        ('BACKGROUND',(0,0), (-1,0),  naranja),
        ('ALIGN',     (1,0), (-1,-1), 'CENTER'),
        ('ALIGN',     (0,0), (0,-1),  'LEFT'),
        ('VALIGN',    (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME',  (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',  (0,1), (-1,-1), 9),
        ('TEXTCOLOR', (0,1), (-1,-1), azul),
        ('BACKGROUND',(0,1), (-1,-1), colors.white),
        ('PADDING',   (0,0), (-1,-1), 8),
        ('GRID',      (0,0), (-1,-1), 0.5, borde),
        ('FONTNAME',  (-1,-1),(-1,-1),'Helvetica-Bold'),
    ]))
    elementos.append(tabla_det)
    elementos.append(Spacer(1, 0.2*cm))

    # Total
    total_tabla = [['', 'TOTAL A PAGAR:', f'${reserva.total:,.0f} COP']]
    tabla_total = Table(total_tabla, colWidths=[8.5*cm, 4.5*cm, 4*cm])
    tabla_total.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (1,0), (1,0),   11),
        ('FONTSIZE',  (2,0), (2,0),   13),
        ('TEXTCOLOR', (1,0), (1,0),   azul),
        ('TEXTCOLOR', (2,0), (2,0),   naranja),
        ('ALIGN',     (1,0), (-1,-1), 'RIGHT'),
        ('VALIGN',    (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING',   (0,0), (-1,-1), 8),
        ('LINEABOVE', (1,0), (-1,0),  2, naranja),
        ('BACKGROUND',(1,0), (-1,0),  gris_claro),
    ]))
    elementos.append(tabla_total)
    elementos.append(Spacer(1, 0.5*cm))

    # Pago
    try:
        pago = reserva.pago
        pago_header = Table([[Paragraph('INFORMACIÓN DE PAGO', ParagraphStyle(
            'sec2', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER
        ))]], colWidths=[17*cm])
        pago_header.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), azul),
            ('PADDING',    (0,0), (-1,-1), 7),
        ]))
        elementos.append(pago_header)

        pago_tabla = [
            ['Referencia:', pago.referencia,          'Método:', pago.get_metodo_display()],
            ['Estado:',     pago.get_estado_display(), 'Fecha:', pago.fecha_pago.strftime('%d/%m/%Y %H:%M')],
        ]
        tabla_pago = Table(pago_tabla, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 4.5*cm])
        tabla_pago.setStyle(TableStyle([
            ('FONTNAME',       (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME',       (2,0), (2,-1), 'Helvetica-Bold'),
            ('FONTNAME',       (1,0), (1,-1), 'Helvetica'),
            ('FONTNAME',       (3,0), (3,-1), 'Helvetica'),
            ('FONTSIZE',       (0,0), (-1,-1), 9),
            ('TEXTCOLOR',      (0,0), (-1,-1), azul),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, gris_claro]),
            ('PADDING',        (0,0), (-1,-1), 7),
            ('GRID',           (0,0), (-1,-1), 0.5, borde),
        ]))
        elementos.append(tabla_pago)
        elementos.append(Spacer(1, 0.5*cm))
    except:
        pass

    # Solicitudes
    try:
        if reserva.solicitudes and reserva.solicitudes.strip():
            sol_header = Table([[Paragraph('SOLICITUDES ESPECIALES', ParagraphStyle(
                'sec3', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER
            ))]], colWidths=[17*cm])
            sol_header.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), azul),
                ('PADDING',    (0,0), (-1,-1), 7),
            ]))
            elementos.append(sol_header)
            sol_tabla = Table([[Paragraph(reserva.solicitudes, ParagraphStyle(
                'sol', fontSize=9, textColor=azul, fontName='Helvetica', leading=14
            ))]], colWidths=[17*cm])
            sol_tabla.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.white),
                ('PADDING',    (0,0), (-1,-1), 10),
                ('GRID',       (0,0), (-1,-1), 0.5, borde),
            ]))
            elementos.append(sol_tabla)
            elementos.append(Spacer(1, 0.5*cm))
    except:
        pass

    # Pie de página
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(HRFlowable(width="100%", thickness=2, color=naranja))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph(
        '¡Gracias por elegir Hotel Casa Marco! Esperamos que disfrute su estadía.',
        ParagraphStyle('gracias', fontSize=10, textColor=azul, fontName='Helvetica-Bold', alignment=TA_CENTER)
    ))
    elementos.append(Spacer(1, 0.15*cm))
    elementos.append(Paragraph(
        f'Documento generado el {reserva.fecha_reserva.strftime("%d/%m/%Y")} — '
        'Este documento es válido como comprobante oficial de reserva.',
        ParagraphStyle('pie', fontSize=8, textColor=gris, fontName='Helvetica', alignment=TA_CENTER)
    ))

    doc.build(elementos)
    return response