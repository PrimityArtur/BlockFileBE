import json

from django.http import JsonResponse, Http404, HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from . import repository as repo
from . import services as serv


def _build_abs(request, relative_url: str) -> str:
    """
    Convierte una URL relativa (ej. /vista/imagen/1/) en absoluta
    para que el móvil tenga la URL completa.
    """
    return request.build_absolute_uri(relative_url)


@require_http_methods(["GET"])
def api_detalle_producto(request, producto_id: int):
    """
    GET /apimovil/productos/<id>/
      -> JSON con detalle del producto + comentarios
    """
    # si hay usuario logueado, obtén su id para saldo_cliente y mostrar_acciones
    cliente_id = request.session.get("usuario_id")
    # user = getattr(request, "user", None)
    # if getattr(user, "is_authenticated", False):
    #     # adapta si tu modelo se llama diferente
    #     cliente_id = getattr(user, "id_usuario", None)

    detalle = repo.obtener_detalle_producto(producto_id, cliente_id=cliente_id)
    if not detalle:
        raise Http404("Producto no encontrado")

    comentarios = repo.listar_comentarios_producto(producto_id)

    # detalle es típicamente un dict; ajusta claves según tu repo
    imagen_urls = []
    for img_id in detalle.get("imagen_ids") or []:
        rel = reverse("vistaProducto:api_imagen", args=[img_id])

        imagen_urls.append(_build_abs(request, rel))

    # URLs de descarga
    url_descarga_ttl = _build_abs(
        request,
        reverse("vistaProducto:download_producto_ttl", args=[producto_id]),
    )
    url_descargar_producto = _build_abs(
        request,
        reverse("vistaProducto:descargar_producto", args=[producto_id]),
    )

    data = {
        "ok": True,
        "producto": {
            "id": detalle.get("id"),
            "nombre": detalle.get("nombre"),
            "descripcion": detalle.get("descripcion"),
            "precio": float(detalle.get("precio")) if detalle.get("precio") is not None else None,
            "saldo_cliente": (
                float(detalle.get("saldo_cliente"))
                if detalle.get("saldo_cliente") is not None
                else None
            ),
            "compras": detalle.get("compras") or 0,
            "calificacion_promedio": float(detalle.get("calificacion_promedio") or 0),
            "autor": detalle.get("autor") or "-",
            "version": detalle.get("version") or "-",
            "categoria": detalle.get("categoria") or "-",
            "fecha_publicacion": (
                detalle.get("fecha_publicacion").isoformat()
                if detalle.get("fecha_publicacion") is not None
                else None
            ),
            "imagen_urls": imagen_urls,
            # "mostrar_acciones": bool(detalle.get("mostrar_acciones", False)),
            "mostrar_acciones": bool(detalle.get("cliente_compro", False)),
            "url_ttl": url_descarga_ttl,
            "url_descargar": url_descargar_producto,
        },
        "comentarios": [
            {
                "cliente": c.get("cliente"),
                "calificacion": c.get("calificacion") or 0,
                "fecha": c.get("fecha").isoformat() if c.get("fecha") else None,
                "descripcion": c.get("descripcion"),
            }
            for c in comentarios
        ],
    }
    return JsonResponse(data, status=200)


@require_http_methods(["GET"])
def descargar_producto_movil_view(request, producto_id: int):
    """
    GET /apimovil/productos/<producto_id>/descargar/

    Requisitos:
      - Debe existir usuario_id en sesión (login móvil hecho).
      - Ese usuario debe haber comprado el producto.

    Responde con el archivo binario.
    """
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return HttpResponseForbidden("Debe iniciar sesión para descargar este producto.")

    # Verificar que el usuario compró este producto
    if not repo.existe_compra(producto_id, usuario_id):
        return HttpResponseForbidden("Este producto no ha sido comprado por este usuario.")

    try:
        filename, contenido, mime = serv.descargar_producto(producto_id)
    except Exception:
        raise Http404("Producto no encontrado o sin archivo asociado.")

    resp = HttpResponse(contenido, content_type=mime)
    resp["Content-Disposition"] = f'attachment; filename=\"{filename}\"'
    resp["Content-Length"] = str(len(contenido))
    return resp



@csrf_exempt
@require_http_methods(["POST"])
def comentar_producto_movil_view(request, producto_id: int):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return HttpResponseForbidden("Debe iniciar sesión para comentar este producto.")

    if not repo.existe_compra(producto_id, usuario_id):
        return HttpResponseForbidden("Solo puede comentar productos que ha comprado.")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"ok": False, "message": "JSON inválido."},
            status=400
        )

    descripcion = (payload.get("descripcion") or "").strip()
    if not descripcion:
        return JsonResponse(
            {"ok": False, "message": "La descripción del comentario es obligatoria."},
            status=400
        )

    # Podrías limitar longitud si quieres:
    if len(descripcion) > 1000:
        return JsonResponse(
            {"ok": False, "message": "El comentario es demasiado largo (máx. 1000 caracteres)."},
            status=400
        )

    # Registrar comentario
    repo.comentar_producto(producto_id, usuario_id, descripcion)

    # Opcional: devolver comentarios actualizados
    comentarios = repo.listar_comentarios_producto(producto_id)

    return JsonResponse(
        {
            "ok": True,
            "message": "Comentario registrado correctamente.",
            "comentarios": comentarios,
        },
        status=201,
    )