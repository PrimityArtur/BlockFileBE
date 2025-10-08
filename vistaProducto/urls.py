from django.urls import path
from . import views

app_name = 'vistaProducto'

urlpatterns = [
    path("producto/<int:producto_id>/", views.detalle_producto_view, name="detalle_producto"),

    path("producto/api/imagen/<int:id_imagen>/", views.api_imagen_producto, name="api_imagen"),

    path("producto/api/<int:producto_id>/descargar/", views.descargar_producto_view, name="descargar_producto"),
    path("producto/api/<int:producto_id>/calificar/", views.calificar_producto_view, name="calificar_producto"),
    path("producto/api/<int:producto_id>/comentar/", views.comentar_producto_view, name="comentar_producto"),
]
