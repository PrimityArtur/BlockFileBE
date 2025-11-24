from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from . import repository as repo

MOBILE_PER_PAGE = 6


@require_http_methods(["GET"])
def api_ranking_productos_mas_comprados(request):
    """
    GET /apimovil/rankings/productos-mas-comprados/?page=1
    """
    try:
        page = int(request.GET.get("page", "1") or 1)
    except ValueError:
        page = 1

    filas, total_pages = repo.ranking_productos_mas_comprados(page, MOBILE_PER_PAGE)
    return JsonResponse(
        {
            "ok": True,
            "rows": filas,
            "page": page,
            "total_pages": total_pages,
        },
        status=200,
    )


@require_http_methods(["GET"])
def api_ranking_mejores_compradores(request):
    """
    GET /apimovil/rankings/mejores-compradores/?page=1
    """
    try:
        page = int(request.GET.get("page", "1") or 1)
    except ValueError:
        page = 1

    filas, total_pages = repo.ranking_mejores_compradores(page, MOBILE_PER_PAGE)
    return JsonResponse(
        {
            "ok": True,
            "rows": filas,
            "page": page,
            "total_pages": total_pages,
        },
        status=200,
    )


@require_http_methods(["GET"])
def api_ranking_productos_mejor_calificados(request):
    """
    GET /apimovil/rankings/productos-mejor-calificados/?page=1
    """
    try:
        page = int(request.GET.get("page", "1") or 1)
    except ValueError:
        page = 1

    filas, total_pages = repo.ranking_productos_mejor_calificados(page, MOBILE_PER_PAGE)
    return JsonResponse(
        {
            "ok": True,
            "rows": filas,
            "page": page,
            "total_pages": total_pages,
        },
        status=200,
    )
