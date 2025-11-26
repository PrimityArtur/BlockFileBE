# gestorCategorias/api_urls.py
from django.urls import path
from . import api_views as api

app_name = "gestorCategorias_movil"

urlpatterns = [
    path("listar/", api.AdminCategoriasListMovilView.as_view(), name="admin_categorias_listar"),
    path("detalle/<int:pk>/", api.AdminCategoriaDetalleMovilView.as_view(), name="admin_categorias_detalle"),
    path("guardar/", api.AdminCategoriaGuardarMovilView.as_view(), name="admin_categorias_guardar"),
    path("eliminar/<int:pk>/", api.AdminCategoriaEliminarMovilView.as_view(), name="admin_categorias_eliminar"),
]
