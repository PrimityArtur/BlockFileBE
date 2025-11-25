from django.urls import path
from . import api_views as api

app_name = "gestorProductos_movil"

urlpatterns = [
    path("", api.AdminProductosListMovilView.as_view(), name="admin_productos_list"),
    # /apimovil/admin/productos/detalle/ID/
    path("detalle/<int:pk>/", api.AdminProductoDetalleMovilView.as_view(), name="admin_productos_detalle"),

    # /apimovil/admin/productos/guardar/
    path("guardar/", api.AdminProductoGuardarMovilView.as_view(), name="admin_productos_guardar"),


    path("archivo/", api.AdminProductoArchivoMovilView.as_view(), name="admin_productos_archivo"),
    path("imagenes/agregar/", api.AdminProductoImagenAgregarMovilView.as_view(), name="admin_productos_imagen_agregar"),
    path("imagenes/reordenar/", api.AdminProductoImagenReordenarMovilView.as_view(), name="admin_productos_imagen_reordenar"),
    path("imagenes/borrar/", api.AdminProductoImagenBorrarMovilView.as_view(), name="admin_productos_imagen_borrar"),

    path(
        "imagenes/archivo/<int:pk>/",
        api.AdminProductoImagenArchivoMovilView.as_view(),
        name="admin_productos_imagen_archivo",
    ),
]