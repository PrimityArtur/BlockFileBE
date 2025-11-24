from django.urls import path
from . import api

app_name = "catalogo_movil"

urlpatterns = [
    path("", api.api_listar_productos_movil, name="listar"),
    path("imagen/<int:id_imagen>/", api.api_imagen_producto_movil, name="imagen"),
]
