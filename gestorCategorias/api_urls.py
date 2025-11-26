from django.urls import path
from . import api_views as api

app_name = "gestorProductos_movil"
urlpatterns = [
    path(
        "listar/",
        api.AdminCategoriasListApi.as_view(),
        name="apimovil_admin_categorias_listar",
    ),
    path(
        "detalle/<int:id_categoria>/",
        api.AdminCategoriasDetalleApi.as_view(),
        name="apimovil_admin_categorias_detalle",
    ),
    path(
        "guardar/",
        api.AdminCategoriasGuardarApi.as_view(),
        name="apimovil_admin_categorias_guardar",
    ),
    path(
        "eliminar/<int:id_categoria>/",
        api.AdminCategoriasEliminarApi.as_view(),
        name="apimovil_admin_categorias_eliminar",
    ),

]