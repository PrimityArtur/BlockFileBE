import magic

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, Http404, HttpResponseForbidden

from core.models import ImagenProducto
from . import repository as repo
from . import services as serv
from . import serializer as serial


@require_http_methods(["GET", "POST"])
def detalle_producto_view(request, producto_id: int):
    cliente_id = request.session.get("usuario_id")
    # Para comprar el producto
    if request.method == "POST":
        if not cliente_id:
            return HttpResponseForbidden("Debes iniciar sesión para comprar.")
        _res = repo.registrar_compra(producto_id, cliente_id)

    detalle = repo.obtener_detalle_producto(producto_id, cliente_id)
    if not detalle:
        raise Http404("Producto no encontrado")

    comentarios = repo.listar_comentarios_producto(producto_id)

    ctx = {
        "p": detalle,
        "comentarios": comentarios,
        "mostrar_acciones": detalle.get("cliente_compro", False),
    }
    return render(request, "products/VistaProducto.html", ctx)

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

@require_http_methods(["POST"])
def descargar_producto_view(request, producto_id: int):
    filename, contenido, mime = serv.descargar_producto(producto_id)

    resp = HttpResponse(contenido, content_type=mime)
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp["Content-Length"] = str(len(contenido))
    return resp

@require_http_methods(["POST"])
def calificar_producto_view(request, producto_id: int):
    usuario_id = request.session.get("usuario_id")
    data = {"calificacion": request.POST.get("calificacion")}

    ser = serial.CalificarProductoSerializer(data=data)
    if not ser.is_valid(): print(ser.errors)
    cal = ser.validated_data["calificacion"]

    serv.calificar_producto(producto_id=producto_id, usuario_id=usuario_id, calificacion=cal)

    return JsonResponse({"ok": True, "producto_id": producto_id, "calificacion": cal})

@require_http_methods(["POST"])
def comentar_producto_view(request, producto_id: int):
    usuario_id = request.session.get("usuario_id")
    data = {"descripcion": request.POST.get("descripcion")}

    ser = serial.ComentarProductoSerializer(data=data)
    if not ser.is_valid(): print(ser.errors)
    descripcion = ser.validated_data["descripcion"]

    serv.comentar_producto(producto_id=producto_id, usuario_id=usuario_id, descripcion=descripcion)

    return JsonResponse({"ok": True, "producto_id": producto_id, "descripcion": descripcion})
