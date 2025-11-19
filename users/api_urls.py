from django.urls import path
from . import api_views as api

app_name = "apimovil"

urlpatterns = [
    path("login/", api.LoginMovilView.as_view(), name="login"),
    path("register/", api.RegisterMovilView.as_view(), name="register"),
]