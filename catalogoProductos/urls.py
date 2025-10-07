from django.urls import path
from . import views

app_name = 'catalogoProductos'

urlpatterns = [
    path('catalogo/', views.catalogo_productos_view, name='catalogo'),

    path("catalogo/api/imagen/<int:id_imagen>/", views.api_imagen_producto, name="api_imagen"),
    path('catalogo/api/listar/', views.api_listar_productos, name='api_listar'),
]
