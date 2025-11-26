from django.urls import path
from . import api_views as api

app_name = "gestorCategorias_movil"

urlpatterns = [
    path(
        "listar/",
        api.AdminCategoriasListMovilView.as_view(),
        name="admin_categorias_listar",
    ),
]
