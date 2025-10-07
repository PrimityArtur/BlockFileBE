import magic

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, Http404
from django.middleware.csrf import get_token
import json

from core.models import ImagenProducto
from . import serializer as serial
from core.utils import PER_PAGE


@require_http_methods(["GET"])
def catalogo_productos_view(request):
    val = serial.catalogoProductosSerializer(data={
        "nombre": (request.GET.get("nombre") or "").strip(),
        "autor": (request.GET.get("autor") or "").strip(),
        "categoria": (request.GET.get("categoria") or "").strip(),
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
            "nombre": data.get("nombre") or "",
            "autor": data.get("autor") or "",
            "categoria": data.get("categoria") or "",
        },
        "csrf_token": get_token(request),
    }
    return render(request, "users/Catalogo.html", ctx)


@require_http_methods(["GET"])
def api_listar_productos(request):
    val = serial.catalogoProductosSerializer(data={
        "nombre": (request.GET.get("nombre") or "").strip(),
        "autor": (request.GET.get("autor") or "").strip(),
        "categoria": (request.GET.get("categoria") or "").strip(),
        "page": request.GET.get("page", "1"),
    })
    if not val.is_valid():
        return JsonResponse({"ok": False, "errors": val.errors}, status=400)
    filas, total_pages = val.listar(per_page=PER_PAGE)
    return JsonResponse({"ok": True, "rows": filas, "page": val.validated_data.get("page", 1), "total_pages": total_pages})


@require_http_methods(["GET"])
def api_imagen_producto(request, id_imagen: int):
    try:
        img = ImagenProducto.objects.only("archivo").get(pk=id_imagen)
    except ImagenProducto.DoesNotExist:
        raise Http404("Imagen no encontrada")

    data = bytes(img.archivo)
    mime = magic.Magic(mime=True)
    content_type = mime.from_buffer(data) or "application/octet-stream" #image/png, image/jpeg, image/webp...
    return HttpResponse(data, content_type=content_type)

