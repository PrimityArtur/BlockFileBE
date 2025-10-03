from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.middleware.csrf import get_token
import json

from . import serializer as serial
from . import services as serv
from core.utils import PER_PAGE

@require_http_methods(["GET"])
def gestion_categorias_view(request):
    val = serial.ValidarCategoriaSerializer(data={
        "id": request.GET.get("id"),
        "nombre": (request.GET.get("nombre") or "").strip(),
        "descripcion": (request.GET.get("descripcion") or "").strip(),
        "page": request.GET.get("page", "1"),
    })
    val.is_valid(raise_exception=False)
    data = val.validated_data if val.is_valid() else {}

    filas, total_pages = val.listar(per_page=PER_PAGE) if val.is_valid() else ([], 1)
    page = int(data.get("page", 1) or 1)

    ctx = {
        "filas": filas,
        "page": page,
        "total_pages": total_pages,
        "filtros": {
            "id": data.get("id") or "",
            "nombre": data.get("nombre") or "",
            "descripcion": data.get("descripcion") or "",
        },
        "csrf_token": get_token(request),
    }
    return render(request, "categories/GestionCategorias.html", ctx)


@require_http_methods(["GET"])
def api_listar_categorias(request):
    val = serial.ValidarCategoriaSerializer(data={
        "id": request.GET.get("id"),
        "nombre": (request.GET.get("nombre") or "").strip(),
        "descripcion": (request.GET.get("descripcion") or "").strip(),
        "page": request.GET.get("page", "1"),
    })
    if not val.is_valid():
        return JsonResponse({"ok": False, "errors": val.errors}, status=400)
    filas, total_pages = val.listar(per_page=PER_PAGE)
    return JsonResponse({"ok": True, "rows": filas, "page": val.validated_data.get("page", 1), "total_pages": total_pages})


@require_http_methods(["GET"])
def api_detalle_categoria(request, id_categoria: int):
    val = serial.DetalleCategoriaEntradaSerializer(data={"id_categoria": id_categoria})
    if not val.is_valid():
        return JsonResponse({"error": "parámetros inválidos"}, status=400)
    d = val.obtener()
    if not d:
        return JsonResponse({"error": "no encontrado"}, status=404)
    return JsonResponse(d)


@require_http_methods(["POST"])
def api_guardar_categoria(request):
    if request.content_type and request.content_type.startswith("application/json"):
        data = json.loads(request.body.decode("utf-8"))
    else:
        data = request.POST.dict()

    val = serial.GuardarCategoriaSerializer(data=data)
    if not val.is_valid():
        return JsonResponse({"errors": val.errors}, status=400)

    res = val.save()
    return JsonResponse({"ok": True, **res})



@require_http_methods(["POST"])
def api_eliminar_categoria(request, id_categoria: int):
    val = serial.EliminarCategoriaSerializer(data={"id_categoria": id_categoria})
    if not val.is_valid():
        return JsonResponse({"errors": val.errors}, status=400)
    val.aplicar()
    return JsonResponse({"ok": True})

