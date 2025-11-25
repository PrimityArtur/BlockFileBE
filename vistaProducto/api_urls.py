from django.urls import path
from . import api

app_name = "vistaProducto_movil"

urlpatterns = [
    path("<int:producto_id>/", api.api_detalle_producto, name="detalle_producto_api"),
    path(
        "<int:producto_id>/descargar/",
        api.descargar_producto_movil_view,
        name="descargar_producto_movil",
    ),
]
