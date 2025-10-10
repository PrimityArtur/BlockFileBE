import magic

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, Http404
from django.middleware.csrf import get_token
import json

from core.models import ImagenProducto
from . import serializer as serial
from . import repository as repo
from core.utils import PER_PAGE


@require_http_methods(["GET"])
def rankings_view(request):
    tab = request.GET.get("tab", "pmc")
    page_pmc   = int(request.GET.get("pmc", 1))
    page_mc    = int(request.GET.get("mc", 1))
    page_pmcal = int(request.GET.get("pmcal", 1))

    pmc_rows, pmc_pages = repo.ranking_productos_mas_comprados(page_pmc, PER_PAGE)
    mc_rows, mc_pages = repo.ranking_mejores_compradores(page_mc, PER_PAGE)
    pmcal_rows, pmcal_pages = repo.ranking_productos_mejor_calificados(page_pmcal, PER_PAGE)

    ctx = {
        "tab": tab,
        "pmc_rows": pmc_rows, "pmc_page": page_pmc, "pmc_pages": pmc_pages,
        "mc_rows": mc_rows, "mc_page": page_mc, "mc_pages": mc_pages,
        "pmcal_rows": pmcal_rows, "pmcal_page": page_pmcal, "pmcal_pages": pmcal_pages,
    }
    return render(request, "products/Rankings.html", ctx)