from django.urls import path
from . import api_views as api

app_name = "gestorProductos_movil"

urlpatterns = [
    path("", api.AdminProductosListMovilView.as_view(), name="admin_productos_list"),
    # /apimovil/admin/productos/detalle/ID/
    path("detalle/<int:pk>/", api.AdminProductoDetalleMovilView.as_view(), name="admin_productos_detalle"),

    # /apimovil/admin/productos/guardar/
    path("guardar/", api.AdminProductoGuardarMovilView.as_view(), name="admin_productos_guardar"),
]