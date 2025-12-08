# catalogoProductos/api.py
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, Http404, HttpResponse

from core.models import ImagenProducto
from . import serializer as serial

# Para móvil queremos 10 productos por página
MOBILE_PER_PAGE = 6


@require_http_methods(["GET"])
def api_listar_productos_movil(request):
    val = serial.catalogoProductosSerializer(data={
        "nombre": (request.GET.get("nombre") or "").strip(),
        "autor": (request.GET.get("autor") or "").strip(),
        "categoria": (request.GET.get("categoria") or "").strip(),
        "page": request.GET.get("page", "1"),
    })

    if not val.is_valid():
        return JsonResponse({"ok": False, "errors": val.errors[next(iter(val.errors))][0]}, status=400)

    filas, total_pages = val.listar(per_page=MOBILE_PER_PAGE)
    return JsonResponse(
        {
            "ok": True,
            "rows": filas,
            "page": val.validated_data.get("page", 1),
            "total_pages": total_pages,
        },
        status=200,
    )


@require_http_methods(["GET"])
def api_imagen_producto_movil(request, id_imagen: int):
    from core.models import ImagenProducto
    import magic

    try:
        img = ImagenProducto.objects.only("archivo").get(pk=id_imagen)
    except ImagenProducto.DoesNotExist:
        raise Http404("Imagen no encontrada")

    data = bytes(img.archivo)
    mime = magic.Magic(mime=True)
    content_type = mime.from_buffer(data) or "application/octet-stream"
    return HttpResponse(data, content_type=content_type)
