from django.urls import path
from . import api

app_name = "perfilcliente_movil"

urlpatterns = [
    path("", api.api_perfil_cliente, name="perfil"),
    path("actualizar/", api.api_actualizar_perfil_cliente, name="actualizar"),
    path("compras/", api.api_compras_cliente, name="compras"),
]
