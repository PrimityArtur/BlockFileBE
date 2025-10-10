from django.urls import path
from . import views

app_name = 'PerfilCliente'

urlpatterns = [
    path('', views.perfil_cliente_view, name='PerfilCliente'),

]
