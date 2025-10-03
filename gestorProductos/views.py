from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.middleware.csrf import get_token
import json

from core.models import ImagenProducto
from . import serializer as serial
from . import services as serv
from core.utils import PER_PAGE


@require_http_methods(["GET"])
def gestion_productos_view(request):
    val = serial.ValidarProductoSerializer(data={
        "id": request.GET.get("id"),
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
            "id": data.get("id") or "",
            "nombre": data.get("nombre") or "",
            "autor": data.get("autor") or "",
            "categoria": data.get("categoria") or "",
        },
        "csrf_token": get_token(request),
    }
    return render(request, "products/GestionProductos.html", ctx)


@require_http_methods(["GET"])
def api_listar_productos(request):
    val = serial.ValidarProductoSerializer(data={
        "id": request.GET.get("id"),
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
def api_detalle_producto(request, id_producto: int):
    val = serial.DetalleProductoEntradaSerializer(data={"id_producto": id_producto})
    if not val.is_valid():
        return JsonResponse({"error": "parámetros inválidos"}, status=400)
    d = val.obtener()
    if not d:
        return JsonResponse({"error": "no encontrado"}, status=404)
    return JsonResponse(d)


@require_http_methods(["POST"])
def api_guardar_producto(request):
    if request.content_type and request.content_type.startswith("application/json"):
        data = json.loads(request.body.decode("utf-8"))
    else:
        data = request.POST.dict()

    val = serial.GuardarProductoSerializer(data=data)
    if not val.is_valid():
        return JsonResponse({"errors": val.errors}, status=400)

    res = val.save()
    return JsonResponse({"ok": True, **res})


@require_http_methods(["POST"])
def api_subir_imagen(request, id_producto: int):
    f = request.FILES.get("archivo")
    if not f:
        return HttpResponseBadRequest("archivo requerido")

    orden = request.POST.get("orden")
    val = serial.ImagenEntradaSerializer(data={
        "id_producto": id_producto,
        "orden": int(orden) if (orden and str(orden).isdigit()) else None
    })
    img_id = serv.agregar_imagen(id_producto=id_producto, contenido=f.read(), orden=orden)
    return JsonResponse({"ok": True, "id_imagen": img_id})


@require_http_methods(["POST"])
def api_borrar_imagen(request, id_imagen: int):
    val = serial.BorrarImagenSerializer(data={"id_imagen": id_imagen})
    if not val.is_valid():
        return JsonResponse({"errors": val.errors}, status=400)
    val.aplicar()
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
def api_reordenar_imagen(request, id_imagen: int):
    nuevo_orden = request.POST.get("orden")
    if not (nuevo_orden and str(nuevo_orden).isdigit()):
        return HttpResponseBadRequest("orden requerido")
    val = serial.ReordenarImagenSerializer(data={"id_imagen": id_imagen, "orden": int(nuevo_orden)})
    if not val.is_valid():
        return JsonResponse({"errors": val.errors}, status=400)
    val.aplicar()
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
def api_eliminar_producto(request, id_producto: int):
    val = serial.EliminarProductoSerializer(data={"id_producto": id_producto})
    if not val.is_valid():
        return JsonResponse({"errors": val.errors}, status=400)
    val.aplicar()
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
def api_imagen_producto(request, id_imagen: int):
    try:
        img = ImagenProducto.objects.get(pk=id_imagen)
    except ImagenProducto.DoesNotExist:
        return HttpResponseBadRequest("no existe")
    return HttpResponse(img.archivo, content_type='image/*')
