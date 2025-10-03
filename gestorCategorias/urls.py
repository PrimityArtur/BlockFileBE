from django.urls import path
from . import views

app_name = 'gestorCategorias'

urlpatterns = [
    path('gestion/', views.gestion_categorias_view, name='gestion'),

    path('gestion/api/detalle/<int:id_categoria>/', views.api_detalle_categoria, name='api_detalle'),
    path('gestion/api/guardar/', views.api_guardar_categoria, name='api_guardar'),

    path('gestion/api/eliminar/<int:id_categoria>/', views.api_eliminar_categoria, name='api_eliminar'),

    path('gestion/api/listar/', views.api_listar_categorias, name='api_listar'),
]
