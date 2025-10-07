
from typing import Optional, Tuple, List, Iterable, Dict, Any
from decimal import Decimal
from django.db.models import Q, Avg, Prefetch
from django.core.paginator import Paginator
from django.db import transaction, connection

from core.models import (
    Producto, Usuario, Cliente, ImagenProducto, DetallesProducto
)
from core.utils import PER_PAGE

def listar_pagina(
    *,
    page:int=1,
    per_page:int=PER_PAGE,
    f_nombre:Optional[str]=None,
    f_autor:Optional[str]=None,
    f_categoria:Optional[str]=None,
) -> Tuple[List[dict], int]:
    page     = max(1, int(page or 1))
    per_page = max(1, int(per_page or PER_PAGE))
    offset   = (page - 1) * per_page
    lo, hi   = offset, offset + per_page

    where, params = ['p.activo = TRUE'], []
    if f_nombre:    where += ['p.nombre ILIKE %s'];    params += [f'%{f_nombre}%']
    if f_autor:     where += ['a.nombre ILIKE %s'];    params += [f'%{f_autor}%']
    if f_categoria: where += ['c.nombre ILIKE %s'];    params += [f'%{f_categoria}%']

    sql = f"""
    WITH base AS (
      SELECT
        p.id_producto                         AS id,
        p.nombre                              AS nombre,
        COALESCE(a.nombre, '')                AS autor,
        img.id_imagen_producto                AS imagen_1_id,
        cal.avg_calificacion                  AS calificacion_promedio,
        COALESCE(comp.cnt_compras, 0)         AS compras,
        COUNT(*)  OVER()                      AS total,
        ROW_NUMBER() OVER (ORDER BY p.id_producto ASC) AS rn
      FROM "PRODUCTO" p
      LEFT JOIN "AUTOR"     a ON a.id_autor     = p.id_autor
      LEFT JOIN "CATEGORIA" c ON c.id_categoria = p.id_categoria
      LEFT JOIN LATERAL (
        SELECT ip.id_imagen_producto
        FROM "IMAGEN_PRODUCTO" ip
        WHERE ip.id_producto = p.id_producto
        ORDER BY ip.orden ASC
        LIMIT 1
      ) img ON TRUE
      LEFT JOIN (
        SELECT id_producto, ROUND(AVG(calificacion)::numeric, 1) AS avg_calificacion
        FROM "CALIFICACION_PRODUCTO"
        GROUP BY id_producto
      ) cal ON cal.id_producto = p.id_producto
      LEFT JOIN (
        SELECT id_producto, COUNT(*)::bigint AS cnt_compras
        FROM "COMPRA_PRODUCTO"
        GROUP BY id_producto
      ) comp ON comp.id_producto = p.id_producto
      WHERE {" AND ".join(where)}
    )
    SELECT id, nombre, autor, imagen_1_id, calificacion_promedio, compras, total
    FROM base
    WHERE rn > %s AND rn <= %s
    ORDER BY id ASC;
    """

    with connection.cursor() as cur:
        cur.execute(sql, params + [lo, hi])
        rows = cur.fetchall()

    total = int(rows[0][-1]) if rows else 0
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1

    filas = [
        {
            "id": pid,
            "nombre": nombre,
            "autor": autor,
            "imagen_1_id": img_id,
            "calificacion_promedio": float(calif) if calif is not None else None,
            "compras": int(compras or 0),
        }
        for pid, nombre, autor, img_id, calif, compras, _ in rows
    ]
    return filas, total_pages

