from django.urls import path
from . import views

app_name = 'rankings'

urlpatterns = [
    path('', views.rankings_view, name='rankings'),

]
