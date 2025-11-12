from django.urls import path
from . import views
from catalogoProductos import views as catProd
app_name = 'users'

urlpatterns = [
    path("", catProd.catalogo_productos_view, name="iniciar"),

    path("iniciar/", views.iniciar_sesion_view, name="iniciar"),
    path("registrarse/", views.registrarse_view, name="registrarse"),
    path("perfil-admin/", views.perfil_admin_view, name="perfil_admin"),
    path("logout/", views.logout_view, name="logout"),
]
