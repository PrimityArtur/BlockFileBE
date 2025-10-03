from django.urls import path
from . import views

app_name = 'gestorUsuario'

urlpatterns = [
    path('gestion/', views.gestion_usuarios_view, name='gestion'),

    path('gestion/api/detalle/<int:id_usuario>/', views.api_detalle_usuario, name='api_detalle'),
    path('gestion/api/guardar/', views.api_guardar_usuario, name='api_guardar'),

    path('gestion/api/eliminar/<int:id_usuario>/', views.api_eliminar_usuario, name='api_eliminar'),

    path('gestion/api/listar/', views.api_listar_usuarios, name='api_listar'),
]
