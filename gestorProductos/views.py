from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.middleware.csrf import get_token
import json
import magic

from core.models import ImagenProducto
from . import serializer as serial
from . import services as serv
from core.utils import PER_PAGE


@require_http_methods(["GET"])
def gestion_productos_view(request):
    val = serial.ValidarProductoSerializer(data={
        "id": request.GET.get("id"),
        "nombre": request.GET.get("nombre", "").strip(),
        "autor": request.GET.get("autor", "").strip(),
        "categoria": request.GET.get("categoria", "").strip(),
        "page": request.GET.get("page", "1"),
    })

    val.is_valid(raise_exception=False)
    data = val.validated_data if val.is_valid() else {}
    filas, total_pages = val.listar(per_page=PER_PAGE) if val.is_valid() else ([], 1)

    ctx = {
        "filas": filas,
        "page": int(data.get("page", 1)),
        "total_pages": total_pages,
        "filtros": {k: (data.get(k) or "") for k in ("id", "nombre", "autor", "categoria")},
        "csrf_token": get_token(request),
    }
    return render(request, "products/GestionProductos.html", ctx)


@require_http_methods(["GET"])
def api_listar_productos(request):
    val = serial.ValidarProductoSerializer(data={
        "id": request.GET.get("id"),
        "nombre": request.GET.get("nombre", "").strip(),
        "autor": request.GET.get("autor", "").strip(),
        "categoria": request.GET.get("categoria", "").strip(),
        "page": request.GET.get("page", "1"),
    })

    val.is_valid(raise_exception=False)
    filas, total_pages = val.listar(per_page=PER_PAGE) if val.is_valid() else ([], 1)
    page = int(val.validated_data.get("page", 1)) if val.is_valid() else 1

    return JsonResponse({
        "ok": True,
        "rows": filas,
        "page": page,
        "total_pages": total_pages
    })


@require_http_methods(["GET"])
def api_detalle_producto(request, id_producto: int):
    ser = serial.DetalleProductoEntradaSerializer(data={"id_producto": id_producto})
    ser.is_valid(raise_exception=False)
    data = ser.obtener()
    return JsonResponse(data or {}, status=200 if data else 404)


@require_http_methods(["POST"])
def api_guardar_producto(request):
    data = (
        json.loads(request.body.decode("utf-8") or "{}")
        if (request.content_type or "").startswith("application/json")
        else request.POST.dict()
    )
    ser = serial.GuardarProductoSerializer(data=data)
    ser.is_valid(raise_exception=False)
    res = ser.save()
    return JsonResponse({"ok": True, **res})


@require_http_methods(["POST"])
def api_subir_imagen(request, id_producto: int):
    archivo = request.FILES.get("archivo")
    if not archivo:
        return HttpResponseBadRequest("archivo requerido")
    orden = request.POST.get("orden")
    img_id = serv.agregar_imagen(
        id_producto=id_producto,
        contenido=archivo.read(),
        orden=int(orden) if str(orden).isdigit() else None
    )
    return JsonResponse({"ok": True, "id_imagen": img_id})

@require_http_methods(["POST"])
def api_borrar_imagen(request, id_imagen: int):
    ser = serial.BorrarImagenSerializer(data={"id_imagen": id_imagen})
    ser.is_valid(raise_exception=False)
    ser.aplicar()
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
def api_reordenar_imagen(request, id_imagen: int):
    orden = request.POST.get("orden")
    if not (orden and str(orden).isdigit()):
        return HttpResponseBadRequest("orden requerido")
    ser = serial.ReordenarImagenSerializer(data={"id_imagen": id_imagen, "orden": int(orden)})
    ser.is_valid(raise_exception=False)
    ser.aplicar()
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
def api_eliminar_producto(request, id_producto: int):
    ser = serial.EliminarProductoSerializer(data={"id_producto": id_producto})
    ser.is_valid(raise_exception=False)
    ser.aplicar()
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
def api_imagen_producto(request, id_imagen: int):
    try:
        img = ImagenProducto.objects.get(pk=id_imagen)
    except ImagenProducto.DoesNotExist:
        return HttpResponseBadRequest("no existe")
    blob = bytes(img.archivo)
    mime_type = magic.from_buffer(blob, mime=True) or "application/octet-stream"
    return HttpResponse(blob, content_type=mime_type)


@require_http_methods(["POST"])
def api_subir_archivo_producto(request, id_producto: int):
    f = request.FILES.get('archivo')
    if not f:
        return HttpResponseBadRequest("archivo requerido")
    serv.subir_archivo_producto_srv(id_producto, f.read())
    return JsonResponse({"ok": True})

@require_http_methods(["GET","POST"])
def descargar_producto_view(request, producto_id: int):
    filename, contenido, mime = serv.descargar_producto(producto_id)

    resp = HttpResponse(contenido, content_type=mime)
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp["Content-Length"] = str(len(contenido))
    return resp