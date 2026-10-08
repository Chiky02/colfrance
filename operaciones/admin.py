from django.contrib import admin

from .models import Alerta, Parada, Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula', 'telefono', 'usuario')
    search_fields = ('nombre', 'cedula', 'telefono', 'usuario__username')


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('maquina', 'usuario', 'fecha')
    search_fields = ('maquina', 'descripcion', 'usuario__username')


@admin.register(Parada)
class ParadaAdmin(admin.ModelAdmin):
    list_display = ('maquina', 'inicio', 'fin', 'usuario', 'cancelada_en')
    search_fields = ('maquina', 'motivo', 'usuario__username')
