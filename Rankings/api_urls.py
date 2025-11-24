from django.urls import path
from . import api

app_name = "rankings_movil"

urlpatterns = [
    path("productos-mas-comprados/", api.api_ranking_productos_mas_comprados, name="pmc"),
    path("mejores-compradores/", api.api_ranking_mejores_compradores, name="mc"),
    path("productos-mejor-calificados/", api.api_ranking_productos_mejor_calificados, name="pmcal"),
]
