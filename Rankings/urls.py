from django.urls import path
from . import views

app_name = 'rankings'

urlpatterns = [
    path('', views.ranking_productos_mas_comprados_view, name='rankingsPMComprados'),

]
