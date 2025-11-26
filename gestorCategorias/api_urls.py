from django.urls import path
from . import api_views as api

app_name = "gestorCategorias_movil"

urlpatterns = [
    # GET lista paginada
    path("", api.AdminCategoriasListMovilView.as_view(), name="admin_categorias_list"),

    # POST guardar (crear/editar)
    path("guardar/", api.AdminCategoriaGuardarMovilView.as_view(), name="admin_categorias_guardar"),

    # POST eliminar
    path("eliminar/", api.AdminCategoriaEliminarMovilView.as_view(), name="admin_categorias_eliminar"),
]
