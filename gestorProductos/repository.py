
from typing import Optional, Tuple, List, Iterable
from decimal import Decimal
from django.db.models import Q, Avg, Prefetch
from django.core.paginator import Paginator
from django.db import transaction

from core.models import (
    Producto, DetallesProducto, Autor, Categoria, ImagenProducto, CalificacionProducto
)
from core.utils import PER_PAGE

def _base_queryset():
    return (
        Producto.objects
        .select_related('autor', 'categoria')
        .prefetch_related(
            Prefetch('imagenes', queryset=ImagenProducto.objects.order_by('orden')),
        )
    )

def listar_pagina(
    *,
    page:int = 1,
    per_page:int = PER_PAGE,
    f_id: Optional[int] = None,
    f_nombre: Optional[str] = None,
    f_autor: Optional[str] = None,
    f_categoria: Optional[str] = None,
) -> Tuple[List[dict], int]:
    qs = _base_queryset()
    if f_id:
        qs = qs.filter(id_producto=f_id)
    if f_nombre:
        qs = qs.filter(nombre__icontains=f_nombre)
    if f_autor:
        qs = qs.filter(autor__nombre__icontains=f_autor)
    if f_categoria:
        qs = qs.filter(categoria__nombre__icontains=f_categoria)

    # annotate promedio calificacion
    qs = qs.annotate(promedio=Avg('calificaciones__calificacion')).order_by('id_producto')

    paginator = Paginator(qs, per_page)
    page = max(1, min(page, paginator.num_pages or 1))
    page_obj = paginator.page(page)

    filas = []
    for p in page_obj.object_list:
        filas.append({
            "id": p.id_producto,
            "nombre": p.nombre,
            "autor": p.autor.nombre if p.autor_id else "",
            "categoria": p.categoria.nombre if p.categoria_id else "",
            "promedio": float(p.promedio) if p.promedio is not None else None,
        })
    return filas, paginator.num_pages or 1

def obtener_producto_detalle(id_producto:int) -> Optional[dict]:
    try:
        p = (
            _base_queryset()
            .get(id_producto=id_producto)
        )
    except Producto.DoesNotExist:
        return None

    det = getattr(p, 'detalles', None)
    promedio = (
        CalificacionProducto.objects
        .filter(producto=p)
        .aggregate(Avg('calificacion'))['calificacion__avg']
    )
    imagenes = [
        {"id": img.id_imagen_producto, "orden": img.orden}
        for img in p.imagenes.all()
    ]
    return {
        "id": p.id_producto,
        "nombre": p.nombre,
        "fecha": p.fecha.isoformat(),
        "calificacion": float(promedio) if promedio is not None else None,
        "descripcion": det.descripcion if det else "",
        "version": det.version if det else "",
        "precio": str(det.precio) if det else "0.00",
        "categoria_id": p.categoria_id,
        "categoria": p.categoria.nombre if p.categoria_id else "",
        "autor_id": p.autor_id,
        "autor": p.autor.nombre if p.autor_id else "",
        "imagenes": imagenes,
        "activo": p.activo,
    }

@transaction.atomic
def crear_actualizar_producto(
    *,
    id_producto: Optional[int],
    nombre: str,
    descripcion: str,
    version: str,
    precio: Decimal,
    id_autor: Optional[int],
    id_categoria: Optional[int],
    activo: bool = True,
) -> int:
    if id_autor:
        autor = Autor.objects.get(pk=id_autor)
    else:
        autor = None
    if id_categoria:
        categoria = Categoria.objects.get(pk=id_categoria)
    else:
        categoria = None

    if id_producto:
        p = Producto.objects.select_for_update().get(pk=id_producto)
        p.nombre = nombre
        p.autor = autor
        p.categoria = categoria
        p.activo = activo
        p.save(update_fields=['nombre','autor','categoria','activo'])
    else:
        # archivo binario del producto principal: por ahora vacío; se actualizará en otra pantalla
        p = Producto.objects.create(nombre=nombre, autor=autor, categoria=categoria, activo=activo, archivo=b"")
    # detalles
    DetallesProducto.objects.update_or_create(
        producto=p,
        defaults={"descripcion": descripcion, "version": version, "precio": precio},
    )
    return p.id_producto

@transaction.atomic
def agregar_imagen_binaria(id_producto:int, *, contenido:bytes, orden:Optional[int]=None) -> int:
    p = Producto.objects.get(pk=id_producto)
    if orden is None:
        ultimo = ImagenProducto.objects.filter(producto=p).order_by('-orden').first()
        orden = (ultimo.orden + 1) if ultimo else 1
    img = ImagenProducto.objects.create(producto=p, orden=orden, archivo=contenido)
    return img.id_imagen_producto

@transaction.atomic
def borrar_imagen(id_imagen:int) -> None:
    ImagenProducto.objects.filter(pk=id_imagen).delete()

@transaction.atomic
def reordenar_imagen(id_imagen:int, nuevo_orden:int) -> None:
    img = ImagenProducto.objects.select_for_update().get(pk=id_imagen)
    img.orden = nuevo_orden
    img.save(update_fields=['orden'])

@transaction.atomic
def eliminar_producto(id_producto:int) -> None:
    Producto.objects.filter(pk=id_producto).delete()


