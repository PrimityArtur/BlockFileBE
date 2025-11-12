import magic
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from core.models import ImagenProducto
from . import repository as repo
from . import serializer as serial
from . import services as serv


@require_http_methods(["GET", "POST"])
def detalle_producto_view(request, producto_id: int):
    cliente_id = request.session.get("usuario_id")
    # Para comprar el producto
    if request.method == "POST":
        if not cliente_id:
            return HttpResponseForbidden("Debes iniciar sesión para comprar.")

        result = serv.validar_y_registrar_compra(producto_id, cliente_id)
        if result == "created":
            messages.success(request, "¡Compra realizada con éxito!")
        elif result == "exists":
            messages.info(request, "Ya habías comprado este producto.")
        elif result == "invalid":
            messages.error(request, "Producto no disponible.")
        elif result == "insufficient":
            messages.error(request, "Saldo insuficiente.")
        elif result == "no_cliente":
            messages.error(request, "No se encontró el cliente.")
        return redirect(request.path)

    # cargar detalles
    detalle = repo.obtener_detalle_producto(producto_id, cliente_id)
    if not detalle:
        raise Http404("Producto no encontrado")

    comentarios = repo.listar_comentarios_producto(producto_id)

    if "text/turtle" in request.headers.get("Accept", ""):
        turtle = _producto_turtle(detalle, len(comentarios), request)
        return HttpResponse(turtle, content_type="text/turtle; charset=utf-8")

    ctx = {
        "p": detalle,
        "comentarios": comentarios,
        "mostrar_acciones": detalle.get("cliente_compro", False),
        "BASE_URL": request.build_absolute_uri('/').rstrip('/'),
        "COMENTARIOS_COUNT": len(comentarios),
    }
    return render(request, "products/VistaProducto.html", ctx)


@require_http_methods(["GET"])
def producto_ttl_view(request, producto_id: int):
    detalle = repo.obtener_detalle_producto(producto_id, cliente_id=None)
    if not detalle:
        raise Http404("Producto no encontrado")

    comentarios = repo.listar_comentarios_producto(producto_id)
    turtle = _producto_turtle(detalle, len(comentarios), request)
    return HttpResponse(turtle, content_type="text/turtle; charset=utf-8")

@require_http_methods(["GET"])
def download_producto_ttl_view(request, producto_id: int):
    detalle = repo.obtener_detalle_producto(producto_id, cliente_id=None)
    if not detalle:
        raise Http404("Producto no encontrado")

    comentarios = repo.listar_comentarios_producto(producto_id)
    turtle = _producto_turtle(detalle, len(comentarios), request)

    # Crear archivo
    filename = f"{detalle.get("nombre")}-{producto_id}.ttl"

    # Responder con descarga forzada
    response = HttpResponse(turtle, content_type="text/turtle; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

@require_http_methods(["GET"])
def api_imagen_producto(request, id_imagen: int):
    try:
        img = ImagenProducto.objects.only("archivo").get(pk=id_imagen)
    except ImagenProducto.DoesNotExist:
        raise Http404("Imagen no encontrada")

    data = bytes(img.archivo)
    mime = magic.Magic(mime=True)
    content_type = mime.from_buffer(data) or "application/octet-stream"  # image/png, image/jpeg, image/webp...
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


def _build_absolute(request, path: str) -> str:
    return request.build_absolute_uri(path)


def _producto_turtle(detalle: dict, comentarios_count: int, request) -> str:
    """
    Construye el RDF Turtle para el producto usando los campos disponibles en `detalle`.
    Incluye autor (como recurso schema:Person), fecha de publicación y categoría.
    """

    # URL base del producto
    base_product_url = _build_absolute(request, reverse('vistaProducto:detalle_producto', args=[detalle["id"]]))

    # Generar slug estable para categoría
    categoria_nombre = (detalle.get("categoria") or "").strip() or "sin-categoria"
    categoria_slug = slugify(categoria_nombre) or "sin-categoria"
    categoria_url = _build_absolute(request, f"/categoria/{categoria_slug}")

    # Generar slug estable para autor
    autor_nombre = (detalle.get("autor") or "").strip() or "autor-desconocido"
    autor_slug = slugify(autor_nombre) or "autor-desconocido"
    autor_url = _build_absolute(request, f"/autor/{autor_slug}")

    # Imagen principal (si hay)
    imagen_ids = detalle.get("imagen_ids") or []
    image_url = ""
    if imagen_ids:
        image_url = _build_absolute(request, reverse('vistaProducto:api_imagen', args=[imagen_ids[0]]))

    # Escapar comillas en literales Turtle
    def q(s: str) -> str:
        if s is None:
            return ""
        return str(s).replace('"', '\\"')

    fecha = detalle.get("fecha_publicacion")
    fecha_iso = ""
    if fecha:
        try:
            fecha_iso = fecha.isoformat()[:10]  # yyyy-mm-dd
        except Exception:
            fecha_iso = str(fecha)

    precio = detalle.get("precio")
    rating = detalle.get("calificacion_promedio")

    # Cabeceras RDF
    turtle = f"""@prefix schema: <https://schema.org/> .
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .

<{base_product_url}>
    rdf:type schema:Product ;
    schema:name "{q(detalle.get('nombre'))}" ;
    schema:description "{q(detalle.get('descripcion'))}" ;
    schema:sku "{detalle.get('id')}" ;
"""

    # Autor como recurso
    if autor_nombre:
        turtle += f'    schema:author <{autor_url}> ;\n'

    # Fecha de publicación
    if fecha_iso:
        turtle += f'    schema:datePublished "{fecha_iso}"^^xsd:date ;\n'

    # Imagen principal
    if image_url:
        turtle += f'    schema:image <{image_url}> ;\n'

    turtle += f'    schema:category <{categoria_url}> ;\n'

    # Categoría y oferta
    turtle += f"""    schema:offers [
        rdf:type schema:Offer ;
        schema:price "{'' if precio is None else precio}" ;
        schema:priceCurrency "PEN" ;
        schema:availability <https://schema.org/InStock>
    ] ;
"""

#     # Calificación
#     if rating is not None:
#         turtle += f"""    schema:aggregateRating [
#         rdf:type schema:AggregateRating ;
#         schema:ratingValue "{rating}" ;
#         schema:reviewCount "{comentarios_count}"
#     ] ;
# """

    # Cierre del bloque del producto
    turtle += f""".
<{categoria_url}>
    rdf:type schema:CategoryCode ;
    schema:name "{q(categoria_nombre)}" ;
    schema:hasPart <{base_product_url}> .
"""

    # Descripción del autor como persona
    if autor_nombre:
        turtle += f"""
<{autor_url}>
    rdf:type schema:Person ;
    schema:name "{q(autor_nombre)}" ;
    schema:hasPart <{base_product_url}> .
"""
    return turtle

