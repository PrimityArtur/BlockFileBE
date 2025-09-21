from django.contrib import admin
from .models import Usuario, Administrador, Cliente
# Register your models here.

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nombre_usuario', 'correo')
    search_fields = ('nombre_usuario', 'correo')

@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'acceso')
    search_fields = ('usuario__nombre_usuario',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'saldo', 'excliente', 'fecha_creacion')
    list_filter = ('excliente',)
    search_fields = ('usuario__nombre_usuario', 'usuario__correo')
