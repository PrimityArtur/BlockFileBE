from django.urls import path
from . import views

app_name = 'vistaProducto'

urlpatterns = [
    path('producto/', views.catalogo_productos_view, name='catalogo'),

    path("producto/api/imagen/<int:id_imagen>/", views.api_imagen_producto, name="api_imagen"),
    path('producto/api/listar/', views.api_listar_productos, name='api_listar'),
]
