from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from . import repository as repo

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
