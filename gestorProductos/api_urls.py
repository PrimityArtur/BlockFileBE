from django.urls import path
from . import api_views as api

app_name = "gestorProductos_movil"

urlpatterns = [
    path("", api.AdminProductosListMovilView.as_view(), name="admin_productos_list"),
]
