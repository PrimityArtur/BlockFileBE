
from typing import Optional, Tuple, List, Iterable
from decimal import Decimal
from django.db.models import Q, Avg, Prefetch
from django.core.paginator import Paginator
from django.db import transaction

from core.models import Categoria
from core.utils import PER_PAGE


def listar_pagina(
    *,
    page:int = 1,
    per_page:int = PER_PAGE,
    f_id: Optional[int] = None,
    f_nombre: Optional[str] = None,
    f_descripcion: Optional[str] = None,
) -> Tuple[List[dict], int]:
    qs = Categoria.objects.all()
    if f_id:
        qs = qs.filter(id_categoria=f_id)
    if f_nombre:
        qs = qs.filter(nombre__icontains=f_nombre)
    if f_descripcion:
        qs = qs.filter(descripcion__icontains=f_descripcion)

    paginator = Paginator(qs, per_page)
    page = max(1, min(page, paginator.num_pages or 1))
    page_obj = paginator.page(page)

    filas = []
    for p in page_obj.object_list:
        filas.append({
            "id": p.id_categoria,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
        })
    return filas, paginator.num_pages or 1

def obtener_categoria_detalle(id_categoria:int) -> Optional[dict]:
    try:
        p = Categoria.objects.get(pk=id_categoria)
    except Categoria.DoesNotExist:
        return None

    return {
        "id": p.id_categoria,
        "nombre": p.nombre,
        "fecha": p.fecha.isoformat(),
        "descripcion": p.descripcion,
    }

@transaction.atomic
def crear_actualizar_categoria(
    *,
    id_categoria: Optional[int],
    nombre: str,
    descripcion: str,
) -> int:

    if id_categoria:
        p = Categoria.objects.select_for_update().get(pk=id_categoria)
        p.nombre = nombre
        p.descripcion = descripcion
        p.save(update_fields=['nombre','descripcion'])
    else:
        # archivo binario del categoria principal: por ahora vacío; se actualizará en otra pantalla
        p = Categoria.objects.create(nombre=nombre, descripcion=descripcion)
    return p.id_categoria

@transaction.atomic
def eliminar_categoria(id_categoria:int) -> None:
    Categoria.objects.filter(pk=id_categoria).delete()


