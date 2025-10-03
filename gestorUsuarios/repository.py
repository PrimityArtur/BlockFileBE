
from typing import Optional, Tuple, List, Iterable
from decimal import Decimal
from django.db.models import Q, Avg, Prefetch
from django.core.paginator import Paginator
from django.db import transaction

from core.models import (
    Usuario, Cliente
)
from core.utils import PER_PAGE

def _base_queryset():
    return (
        Usuario.objects
        .select_related('cliente').filter(cliente__isnull=False).order_by('id_usuario')
    )

def listar_pagina(
    *,
    page:int = 1,
    per_page:int = PER_PAGE,
    f_id: Optional[int] = None,
    f_nombre: Optional[str] = None,
    f_saldo: Decimal = None,
) -> Tuple[List[dict], int]:
    qs = _base_queryset()
    if f_id:
        qs = qs.filter(id_usuario=f_id)
    if f_nombre:
        qs = qs.filter(nombre_usuario__icontains=f_nombre)
    if f_saldo:
        qs = qs.filter(cliente__saldo=f_saldo)

    paginator = Paginator(qs, per_page)
    page = max(1, min(page, paginator.num_pages or 1))
    page_obj = paginator.page(page)

    filas = []
    for p in page_obj.object_list:
        filas.append({
            "id": p.id_usuario,
            "nombre": p.nombre_usuario,
            "saldo": p.cliente.saldo,
        })
    return filas, paginator.num_pages or 1

def obtener_usuario_detalle(id_usuario:int) -> Optional[dict]:
    try:
        p = (
            _base_queryset()
            .get(id_usuario=id_usuario)
        )
    except Usuario.DoesNotExist:
        return None

    det = getattr(p, 'cliente', None)
    print(p)
    return {
        "id": p.id_usuario,
        "nombre": p.nombre_usuario,
        "fecha": det.fecha_creacion.isoformat(),
        "correo": p.correo,
        "saldo": det.saldo,
    }

@transaction.atomic
def actualizar_usuario(
    *,
    id_usuario: Optional[int],
    saldo: Decimal,
) -> int:

    p = Usuario.objects.select_for_update().get(pk=id_usuario)
    # detalles
    Cliente.objects.filter(usuario=p).update(saldo=saldo)
    return p.id_usuario

@transaction.atomic
def eliminar_usuario(id_usuario:int) -> None:
    p = Usuario.objects.select_for_update().get(pk=id_usuario)
    Cliente.objects.filter(usuario=p).update(excliente=True)

