from django.urls import path
from . import views

app_name = 'gestorProductos'

urlpatterns = [
    path('gestion/', views.gestion_productos_view, name='gestion'),

    path('gestion/api/detalle/<int:id_producto>/', views.api_detalle_producto, name='api_detalle'),
    path('gestion/api/guardar/', views.api_guardar_producto, name='api_guardar'),
    path('gestion/api/subir_imagen/<int:id_producto>/', views.api_subir_imagen, name='api_subir_imagen'),
    path('gestion/api/borrar_imagen/<int:id_imagen>/', views.api_borrar_imagen, name='api_borrar_imagen'),
    path('gestion/api/reordenar_imagen/<int:id_imagen>/', views.api_reordenar_imagen, name='api_reordenar_imagen'),
    path('gestion/api/eliminar/<int:id_producto>/', views.api_eliminar_producto, name='api_eliminar'),
    path('gestion/api/imagen/<int:id_imagen>/', views.api_imagen_producto, name='api_imagen'),

    path('gestion/api/listar/', views.api_listar_productos, name='api_listar'),
]
