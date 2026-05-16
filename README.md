#Hotel Casa Marco — Sistema de Gestión Hotelera

Sistema web desarrollado en **Django** para la gestión integral de un hotel, incluyendo reservas, pagos, habitaciones, servicios y más.

#Descripción

Hotel Casa Marco es una plataforma de gestión hotelera que permite a los usuarios reservar habitaciones, gestionar sus estadías y realizar pagos en línea, mientras que los administradores controlan todo el flujo operativo del hotel desde un panel dedicado.


#Tecnologías utilizadas

- **Python 3.14**
- **Django 6.0**
- **MySQL** (base de datos - requiere XAMMP)
- **Bootstrap 5.3**
- **Font Awesome 6.4**
- **Chart.js** (reportes y gráficas)
- **SweetAlert2** (alertas)
- **ReportLab** (generación de PDF)
- **Gmail SMTP** (envío de correos)


#Instalación

#Clonar el repositorio

```bash
git clone https://github.com/yvlyvlyvl/PROYECTO-FINAL-.git
cd hotel-casa-marco
```

#Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

#Instalar dependencias

```bash
pip install django
pip install pillow
pip install reportlab
```

#Configurar base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

#Crear superusuario (administrador)

```bash
python manage.py createsuperuser
```

#Ejecutar el servidor

```bash
python manage.py runserver
```

Abre el navegador en: `http://127.0.0.1:8000/`

#Configuración de correo (Gmail)

En `settings.py` agrega:

```python
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = 'tucorreo@gmail.com'
EMAIL_HOST_PASSWORD = 'tu_contraseña_de_app'
DEFAULT_FROM_EMAIL  = 'tucorreo@gmail.com'
```

> Para obtener la contraseña de aplicación: Google Account → Seguridad → Verificación en dos pasos → Contraseñas de aplicación


#Flujo del Usuario

#Reservar
- Va a **Reservar Habitación**
- Elige habitación → llena datos → presiona Reservar
- Estado: **Pendiente**
- Botones:  Pagar ·  Enviar correo ·  Cancelar

#Pagar
- Presiona  Pagar → elige método → confirma
- En **Mis Pagos** aparece el pago Confirmado 
- Botón  Cancelar Pago visible mientras admin no confirme

#Esperar confirmación del admin
- Cuando el admin confirma → llega correo + notificación
- Estado: **Confirmada**
- Botones: Enviar correo · Descargar Factura · Solicitar Servicio · Cancelar

#Check-in
- Admin hace Check-in → llega correo + notificación
- Estado: **En curso**
- Puede solicitar servicios · Ya no puede cancelar

#Check-out
- Admin hace Check-out → llega correo + notificación
- Reserva pasa a **Historial Estadías**
- Puede Calificar la estadía
- Habitación vuelve a Disponible


#Flujo del Administrador

#Ver reservas nuevas
- En Dashboard ve reservas recientes
- Va a Reservas → ve todas

#Confirmar reserva
- Busca la reserva Pendiente
- Presiona Estado → selecciona Confirmada
- Usuario recibe correo + notificación
- Habitación pasa a Reservada

#Check-in
- Cuando el huésped llega
- Presiona Estado → selecciona Check-in realizado
- Usuario recibe correo + notificación
- Habitación pasa a Ocupada

#Check-out
- Cuando el huésped se va
- Presiona Estado → selecciona Check-out realizado
- Usuario recibe correo + notificación
- Habitación vuelve a Disponible
- Usuario puede Calificar


#Estados de la Reserva

| Estado | Descripción |
|---|---|
| Pendiente | Reserva creada, esperando confirmación del admin |
| Confirmada | Admin confirmó la reserva |
| En curso | Huésped realizó check-in |
| Completada | Huésped realizó check-out |
| Cancelada | Reserva cancelada por usuario o admin |

#Estados de la Habitación

| Estado | Descripción |
|---|---|
|  Disponible | Libre para reservar |
|  Reservada | Reserva confirmada pendiente de check-in |
|  Ocupada | Huésped actualmente en la habitación |
|  Limpieza | En proceso de limpieza |
|  Mantenimiento | En mantenimiento |


#Correos automáticos

| Evento | Destinatario |
|---|---|
| Admin confirma reserva | Usuario |
| Admin hace Check-in | Usuario |
| Admin hace Check-out | Usuario |
| Usuario cancela reserva | Usuario |
| Usuario solicita envío manual | Usuario |

#Funcionalidades

#Usuario
- Registro e inicio de sesión
- Recuperación de contraseña por correo
- Ver habitaciones con fotos y galería
- Ver opiniones de cada habitación
- Reservar habitación
- Gestionar mis reservas
- Realizar pagos
- Enviar reserva al correo
- Descargar factura en PDF
- Solicitar servicios adicionales
- Cancelar reserva
- Historial de estadías
- Calificar estadía con comentario
- Guardar habitaciones en favoritos
- Notificaciones en tiempo real
- Editar perfil y contraseña
- Formulario de contacto

#Administrador
- Dashboard con estadísticas
- Gestión de habitaciones (CRUD)
- Galería de fotos por habitación
- Gestión de reservas con flujo completo
- Correos automáticos al cambiar estado
- Gestión de clientes
- Gestión de pagos
- Gestión de servicios solicitados
- Reportes con gráficas (Chart.js)

#Autores

- **Joey Vergara** — frontend
- **Fabian Muñoz** — fullstack
- **Wilmer caraballo** — Documentador
- **Luis Alejandro Ozuna** — fullstack
- Universidad Cooperativa de Colombia — Proyecto final 2026

#Licencia

Este proyecto fue desarrollado con fines académicos para la Universidad Cooperativa de Colombia.
