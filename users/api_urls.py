from django.urls import path, include
from . import api_views as api

app_name = "apimovil"

urlpatterns = [
    path("login/", api.LoginMovilView.as_view(), name="login"),
    path("register/", api.RegisterMovilView.as_view(), name="register"),

    path("admin/perfil/", api.AdminPerfilMovilView.as_view(), name="api_admin_perfil_movil"),



    path("catalogo/", include("catalogoProductos.api_urls")),
    path("rankings/", include("Rankings.api_urls")),
    path("productos/", include("vistaProducto.api_urls")),
    path("perfil/", include("PerfilCliente.api_urls")),



]