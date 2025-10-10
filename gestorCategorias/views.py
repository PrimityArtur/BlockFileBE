from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.middleware.csrf import get_token
import json

from . import serializer as serial
from . import services as serv
from core.utils import PER_PAGE


def _qcategorias(request):
    g = request.GET
    return {
        "id": g.get("id"),
        "nombre": (g.get("nombre") or "").strip(),
        "descripcion": (g.get("descripcion") or "").strip(),
        "page": g.get("page", "1"),
    }

def _json_body(request):
    if request.content_type and request.content_type.startswith("application/json"):
        try:
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            return {}
    return request.POST.dict()

def _bad(errors, code=400):
    return JsonResponse({"ok": False, "errors": errors}, status=code)

@require_http_methods(["GET"])
def gestion_categorias_view(request):
    val = serial.ValidarCategoriaSerializer(data=_qcategorias(request))
    is_valid = val.is_valid()
    data = val.validated_data if is_valid else {}

    filas, total_pages = (val.listar(per_page=PER_PAGE) if is_valid else ([], 1))
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
    val = serial.ValidarCategoriaSerializer(data=_qcategorias(request))
    if not val.is_valid():
        return _bad(val.errors)
    filas, total_pages = val.listar(per_page=PER_PAGE)
    return JsonResponse({
        "ok": True,
        "rows": filas,
        "page": val.validated_data.get("page", 1),
        "total_pages": total_pages
    })

@require_http_methods(["GET"])
def api_detalle_categoria(request, id_categoria: int):
    val = serial.DetalleCategoriaEntradaSerializer(data={"id_categoria": id_categoria})
    if not val.is_valid():
        return _bad(val.errors)
    d = val.obtener()
    return JsonResponse(d if d else {"ok": False, "error": "no encontrado"}, status=200 if d else 404)



@require_http_methods(["POST"])
def api_guardar_categoria(request):
    data = _json_body(request)
    val = serial.GuardarCategoriaSerializer(data=data)
    if not val.is_valid():
        return _bad(val.errors)
    res = val.save()
    return JsonResponse({"ok": True, **res})



@require_http_methods(["POST"])
def api_eliminar_categoria(request, id_categoria: int):
    val = serial.EliminarCategoriaSerializer(data={"id_categoria": id_categoria})
    if not val.is_valid():
        return _bad(val.errors)
    val.aplicar()
    return JsonResponse({"ok": True})

