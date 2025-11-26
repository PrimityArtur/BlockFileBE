from django.urls import path
from . import api_views as api

app_name = "gestorUsuarios_movil"

urlpatterns = [
    # GET lista paginada
    path("", api.AdminUsuariosListMovilView.as_view(), name="admin_usuarios_list"),

    # GET detalle
    path("detalle/<int:id_usuario>/", api.AdminUsuarioDetalleMovilView.as_view(), name="admin_usuarios_detalle"),

    # POST guardar (actualizar saldo)
    path("guardar/", api.AdminUsuarioGuardarMovilView.as_view(), name="admin_usuarios_guardar"),

    # POST eliminar (excliente = TRUE)
    path("eliminar/", api.AdminUsuarioEliminarMovilView.as_view(), name="admin_usuarios_eliminar"),
]
