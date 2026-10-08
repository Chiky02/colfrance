from django.contrib import admin

from .models import Alerta, Parada


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('maquina', 'usuario', 'fecha')
    search_fields = ('maquina', 'descripcion', 'usuario__username')


@admin.register(Parada)
class ParadaAdmin(admin.ModelAdmin):
    list_display = ('maquina', 'inicio', 'fin', 'usuario', 'cancelada_en')
    search_fields = ('maquina', 'motivo', 'usuario__username')
