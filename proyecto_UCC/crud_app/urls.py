from django.urls import path
from . import views

urlpatterns = [
    # Página principal
    path('', views.pagina_principal, name='pagina_principal'),
    path('dashboard/', views.home, name='home'),

    # Autenticacion
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('registrarse/', views.register_user, name='register'),

    # Perfil
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),

    # Recuperar cuenta
    path('recuperar/', views.recuperar_cuenta, name='recuperar_cuenta'),
    path('verificar-codigo/', views.verificar_codigo, name='verificar_codigo'),
    path('nueva-contrasena/', views.nueva_contrasena, name='nueva_contrasena'),

    # Usuario - Habitaciones
    path('habitaciones/', views.reservar_habitacion, name='reservar_habitacion'),
    path('habitaciones/reservar/<int:hab_pk>/', views.confirmar_reserva, name='confirmar_reserva'),

    # Usuario - Reservas
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('mis-reservas/cancelar/<int:pk>/', views.cancelar_reserva, name='cancelar_reserva'),

    # Usuario - Historial
    path('historial/', views.historial_estadias, name='historial_estadias'),

    # Usuario - Pagos
    path('mis-pagos/', views.mis_pagos, name='mis_pagos'),
    path('mis-pagos/realizar/<int:reserva_pk>/', views.realizar_pago, name='realizar_pago'),

    # Usuario - Notificaciones
    path('notificaciones/', views.notificaciones, name='notificaciones'),

    # Usuario - Favoritos
    path('favoritos/', views.favoritos, name='favoritos'),
    path('favoritos/toggle/<int:hab_pk>/', views.toggle_favorito, name='toggle_favorito'),

    # Admin - Dashboard
    path('home-admin/', views.home_admin, name='home_admin'),

    # Admin - Habitaciones
    path('admin-habitaciones/', views.admin_habitaciones, name='admin_habitaciones'),
    path('admin-habitaciones/crear/', views.admin_crear_habitacion, name='admin_crear_habitacion'),
    path('admin-habitaciones/editar/<int:pk>/', views.admin_editar_habitacion, name='admin_editar_habitacion'),
    path('admin-habitaciones/eliminar/<int:pk>/', views.admin_eliminar_habitacion, name='admin_eliminar_habitacion'),

    # Admin - Reservas
    path('admin-reservas/', views.admin_reservas, name='admin_reservas'),
    path('admin-reservas/estado/<int:pk>/', views.admin_cambiar_estado_reserva, name='admin_cambiar_estado_reserva'),

    # Admin - Clientes
    path('admin-clientes/', views.admin_clientes, name='admin_clientes'),

    # Admin - Pagos
    path('admin-pagos/', views.admin_pagos, name='admin_pagos'),

    # Admin - Servicios
    path('admin-servicios/', views.admin_servicios, name='admin_servicios'),
    path('admin-servicios/estado/<int:pk>/', views.admin_cambiar_estado_servicio, name='admin_cambiar_estado_servicio'),

    # Admin - Reportes
    path('admin-reportes/', views.admin_reportes, name='admin_reportes'),
    
    #contacto
    path('contacto/', views.contacto, name='contacto'),

    #cancelar pagos
    path('mis-pagos/cancelar/<int:pk>/', views.cancelar_pago, name='cancelar_pago'),

    #solicitar servicios
    path('mis-reservas/servicio/<int:reserva_pk>/', views.solicitar_servicio, name='solicitar_servicio'),

    #calificaciones
    path('calificar/<int:reserva_pk>/', views.calificar_estadia, name='calificar_estadia'),
    path('mis-calificaciones/', views.mis_calificaciones, name='mis_calificaciones'),

    #fotohabitaciones
    path('admin-habitaciones/fotos/<int:pk>/', views.admin_fotos_habitacion, name='admin_fotos_habitacion'),
    path('admin-habitaciones/fotos/eliminar/<int:foto_pk>/', views.admin_eliminar_foto, name='admin_eliminar_foto'),

    #descargar factura
    path('mis-reservas/factura/<int:reserva_pk>/', views.descargar_factura, name='descargar_factura'),

    #enviar reserva correo
    path('mis-reservas/enviar-correo/<int:pk>/', views.enviar_correo_reserva, name='enviar_correo_reserva'),
]