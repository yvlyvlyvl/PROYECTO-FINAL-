from django.db import models
from django.contrib.auth.models import User
import random
import string


class Habitacion(models.Model):

    TIPOS = [
        ('estandar',    '🛏️ Estándar'),
        ('deluxe',      '🛏️ Deluxe'),
        ('suite',       '⭐ Suite'),
        ('suite_ejecutiva', '👔 Suite Ejecutiva'),
        ('suite_presidencial', '👑 Suite Presidencial'),
        ('villa',       '🏡 Villa Familiar'),
    ]

    ESTADOS = [
        ('disponible',   '🟢 Disponible'),
        ('reservada',    '📋 Reservada'),
        ('ocupada',      '🔵 Ocupada'),
        ('limpieza',     '🟡 Limpieza'),
        ('mantenimiento','🔴 Mantenimiento'),
    ]

    numero          = models.CharField(max_length=10, unique=True)
    tipo            = models.CharField(max_length=30, choices=TIPOS, default='estandar')
    descripcion     = models.TextField()
    precio_noche    = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad       = models.PositiveIntegerField(default=2)
    piso            = models.PositiveIntegerField(default=1)
    estado          = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    imagen          = models.ImageField(upload_to='habitaciones/', blank=True, null=True)
    imagen_url      = models.URLField(blank=True, null=True)
    amenidades      = models.TextField(blank=True, null=True)
    activa          = models.BooleanField(default=True)
    imagenes_galeria = models.TextField(blank=True, null=True)
    creado_el       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hab {self.numero} — {self.get_tipo_display()}"

    @property
    def amenidades_lista(self):
        if self.amenidades:
            return [a.strip() for a in self.amenidades.split(',')]
        return []


class Reserva(models.Model):

    ESTADOS = [
        ('pendiente',   '⏳ Pendiente'),
        ('confirmada',  '✅ Confirmada'),
        ('cancelada',   '❌ Cancelada'),
        ('completada',  '🏁 Completada'),
        ('en_curso',    '🔵 En curso'),
    ]

    usuario         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    habitacion      = models.ForeignKey(Habitacion, on_delete=models.CASCADE, related_name='reservas')
    codigo          = models.CharField(max_length=10, unique=True)
    estado          = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    check_in        = models.DateField(default='2024-01-01')
    check_out       = models.DateField(default='2024-01-02')

    huespedes       = models.PositiveIntegerField(default=1)
    adultos         = models.PositiveIntegerField(default=1)
    ninos           = models.PositiveIntegerField(default=0)
    total           = models.DecimalField(max_digits=10, decimal_places=2)
    nombre_huesped  = models.CharField(max_length=100, default='')
    documento       = models.CharField(max_length=20, default='')
    telefono        = models.CharField(max_length=20, default='')
    solicitudes     = models.TextField(blank=True, null=True)
    fecha_reserva   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva {self.codigo} — {self.habitacion}"

    @staticmethod
    def generar_codigo():
        return 'HP-' + ''.join(random.choices(string.digits, k=4))

    @property
    def noches(self):
        return (self.check_out - self.check_in).days


class Pago(models.Model):

    METODOS = [
        ('tarjeta',       '💳 Tarjeta'),
        ('transferencia', '🏦 Transferencia'),
        ('efectivo',      '💵 Efectivo'),
        ('pse',           '📱 PSE'),
    ]

    ESTADOS = [
        ('pendiente',    '⏳ Pendiente'),
        ('confirmado',   '✅ Confirmado'),
        ('rechazado',    '❌ Rechazado'),
        ('reembolsado',  '↩️ Reembolsado'),
    ]

    reserva         = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='pago')
    usuario         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagos')
    metodo          = models.CharField(max_length=20, choices=METODOS)
    estado          = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    total           = models.DecimalField(max_digits=10, decimal_places=2)
    referencia      = models.CharField(max_length=20, unique=True)
    comprobante     = models.FileField(upload_to='comprobantes/', blank=True, null=True)
    nombre_titular  = models.CharField(max_length=100, blank=True, null=True)
    numero_tarjeta  = models.CharField(max_length=4, blank=True, null=True)
    banco           = models.CharField(max_length=100, blank=True, null=True)
    fecha_pago      = models.DateTimeField(auto_now_add=True)
    actualizado     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pago {self.referencia} — {self.reserva.codigo}"

    @staticmethod
    def generar_referencia():
        return 'CM-' + ''.join(random.choices(string.digits, k=8))


class Servicio(models.Model):

    TIPOS = [
        ('limpieza',     '🧹 Limpieza'),
        ('room_service', '🍽️ Room Service'),
        ('lavanderia',   '👕 Lavandería'),
        ('spa',          '💆 Spa'),
        ('transporte',   '🚗 Transporte'),
        ('otro',         '📦 Otro'),
    ]

    ESTADOS = [
        ('pendiente',   '⏳ Pendiente'),
        ('en_proceso',  '🔵 En proceso'),
        ('completado',  '✅ Completado'),
        ('cancelado',   '❌ Cancelado'),
    ]

    reserva         = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='servicios')
    tipo            = models.CharField(max_length=20, choices=TIPOS)
    descripcion     = models.TextField(blank=True, null=True)
    estado          = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    costo           = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.reserva.codigo}"


class Notificacion(models.Model):

    TIPOS = [
        ('reserva',  '🛏️ Reserva'),
        ('pago',     '💳 Pago'),
        ('promo',    '⭐ Promoción'),
        ('alerta',   '⚠️ Alerta'),
        ('info',     '📢 Info'),
    ]

    usuario         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo            = models.CharField(max_length=20, choices=TIPOS, default='info')
    titulo          = models.CharField(max_length=100)
    mensaje         = models.TextField()
    leida           = models.BooleanField(default=False)
    creado_el       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} — {self.usuario.username}"


class Favorito(models.Model):
    usuario         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoritos')
    habitacion      = models.ForeignKey(Habitacion, on_delete=models.CASCADE, related_name='favoritos')
    creado_el       = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'habitacion')

    def __str__(self):
        return f"{self.usuario.username} — {self.habitacion}"


class CodigoVerificacion(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    codigo      = models.CharField(max_length=6)
    creado_el   = models.DateTimeField(auto_now_add=True)
    usado       = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} — {self.codigo}"

    @staticmethod
    def generar_codigo():
        import random
        return str(random.randint(100000, 999999))


class Calificacion(models.Model):
    usuario    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones')
    reserva    = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='calificacion')
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE, related_name='calificaciones')
    estrellas  = models.PositiveIntegerField(default=5)
    comentario = models.TextField(blank=True, null=True)
    creado_el  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} — {self.estrellas}⭐ — {self.habitacion}"
    

class FotoHabitacion(models.Model):
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE, related_name='fotos')
    imagen     = models.ImageField(upload_to='habitaciones/galeria/')
    orden      = models.PositiveIntegerField(default=0)
    creado_el  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"Foto de {self.habitacion.numero}"
    

