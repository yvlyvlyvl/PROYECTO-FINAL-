from django.contrib import admin
from .models import Habitacion, Reserva, Pago, Servicio, Notificacion, Favorito, CodigoVerificacion, Calificacion, FotoHabitacion

@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display  = ('numero', 'tipo', 'precio_noche', 'capacidad', 'estado', 'piso')
    search_fields = ('numero',)
    list_filter   = ('tipo', 'estado')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'usuario', 'habitacion', 'check_in', 'check_out', 'estado', 'total')
    search_fields = ('codigo', 'nombre_huesped')
    list_filter   = ('estado',)

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display  = ('referencia', 'usuario', 'metodo', 'estado', 'total', 'fecha_pago')
    list_filter   = ('metodo', 'estado')

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display  = ('tipo', 'reserva', 'estado', 'costo', 'fecha_solicitud')
    list_filter   = ('tipo', 'estado')

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'usuario', 'tipo', 'leida', 'creado_el')
    list_filter   = ('tipo', 'leida')

@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'habitacion', 'creado_el')

@admin.register(CodigoVerificacion)
class CodigoVerificacionAdmin(admin.ModelAdmin):
    list_display  = ('user', 'codigo', 'usado', 'creado_el')

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'habitacion', 'estrellas', 'creado_el')
    list_filter  = ('estrellas',)

@admin.register(FotoHabitacion)
class FotoHabitacionAdmin(admin.ModelAdmin):
    list_display = ('habitacion', 'orden', 'creado_el')