from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path("iniciar/", views.iniciar_sesion_view, name="iniciar"),
    path("registrarse/", views.registrarse_view, name="registrarse"),
    path("catalogo/", views.catalogo_view, name="catalogo"),
    path("perfil-admin/", views.perfil_admin_view, name="perfil_admin"),
    path("perfil-usuario/", views.perfil_usuario_view, name="perfil_usuario"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.iniciar_sesion_view),
]
