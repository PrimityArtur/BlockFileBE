
from typing import Optional, Tuple, List, Iterable, Dict, Any
from decimal import Decimal
from django.db.models import Q, Avg, Prefetch
from django.core.paginator import Paginator
from django.db import transaction, connection

from core.models import (
    Producto, Usuario, Cliente, ImagenProducto, DetallesProducto
)
from core.utils import PER_PAGE


def ranking_productos_mas_comprados(
        page: int,
        per_page: int
) -> Tuple[List[Dict[str, Any]], int]:
    page = max(1, int(page or 1))
    per_page = max(1, int(per_page or 20))
    lo, hi = (page - 1) * per_page, (page - 1) * per_page + per_page

    sql = """
    WITH agg AS (
      SELECT
        p.id_producto,
        p.nombre,
        COALESCE(a.nombre, '') AS autor,
        COALESCE(c.nombre, '') AS categoria,
        d.precio,
        COUNT(co.id_compra_producto)::bigint AS compras
      FROM "PRODUCTO" p
      LEFT JOIN "AUTOR" a      ON a.id_autor     = p.id_autor
      LEFT JOIN "CATEGORIA" c  ON c.id_categoria = p.id_categoria
      LEFT JOIN "DETALLES_PRODUCTO" d ON d.id_producto = p.id_producto
      JOIN "COMPRA_PRODUCTO"  co ON co.id_producto = p.id_producto
      WHERE p.activo = TRUE
      GROUP BY p.id_producto, p.nombre, a.nombre, c.nombre, d.precio
    ),
    ranked AS (
      SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY compras DESC, id_producto ASC) AS top,
        COUNT(*)  OVER () AS total
      FROM agg
    ),
    page_rows AS (
      SELECT *
      FROM ranked
      WHERE top > %s AND top <= %s
      ORDER BY compras DESC, id_producto ASC
    )
    SELECT id_producto, top, nombre, autor, categoria, precio, compras, total
    FROM page_rows;
    """
    with connection.cursor() as cur:
        cur.execute(sql, [lo, hi])
        rows = cur.fetchall()

    total = int(rows[0][-1]) if rows else 0
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1

    data = []
    for r in rows:
        data.append({
            "id": r[0],
            "top": int(r[1]),
            "nombre": r[2],
            "autor": r[3],
            "categoria": r[4],
            "precio": float(r[5]) if r[5] is not None else None,
            "compras": int(r[6]),
        })
    return data, total_pages


def ranking_mejores_compradores(
        page: int,
        per_page: int
) -> Tuple[List[Dict[str, Any]], int]:
    page = max(1, int(page or 1))
    per_page = max(1, int(per_page or 20))
    lo, hi = (page - 1) * per_page, (page - 1) * per_page + per_page

    sql = """
    WITH agg AS (
      SELECT
        u.id_usuario,
        COALESCE(u.nombre_usuario, '') AS nombre,
        COUNT(co.id_compra_producto)::bigint AS compras
      FROM "COMPRA_PRODUCTO" co
      JOIN "USUARIO" u ON u.id_usuario = co.id_usuario
      GROUP BY u.id_usuario, u.nombre_usuario
    ),
    ranked AS (
      SELECT
        *,
        ROW_NUMBER()  OVER (ORDER BY compras DESC, id_usuario ASC) AS top,
        COUNT(*)      OVER ()                                     AS total
      FROM agg
    )
    SELECT id_usuario, top, nombre, compras, total
    FROM ranked
    WHERE top > %s AND top <= %s
    ORDER BY top;
    """
    with connection.cursor() as cur:
        cur.execute(sql, [lo, hi])
        rows = cur.fetchall()

    filas = [{
        "id_usuario": r[0],
        "top": int(r[1]),
        "nombre": r[2],
        "compras": int(r[3]),
    } for r in rows]

    total = int(rows[0][-1]) if rows else 0
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    return filas, total_pages


def ranking_productos_mejor_calificados(
        page: int,
        per_page: int
) -> Tuple[List[Dict[str, Any]], int]:
    page = max(1, int(page or 1))
    per_page = max(1, int(per_page or 20))
    lo, hi = (page - 1) * per_page, (page - 1) * per_page + per_page

    sql = """
    WITH agg AS (
      SELECT
        p.id_producto,
        p.nombre,
        COALESCE(a.nombre,'')    AS autor,
        COALESCE(c.nombre,'')    AS categoria,
        d.precio,
        COUNT(cp.id_calificacion)::bigint          AS n_calificaciones,
        ROUND(AVG(cp.calificacion)::numeric, 1)    AS calif_prom
      FROM "PRODUCTO" p
      LEFT JOIN "AUTOR" a        ON a.id_autor     = p.id_autor
      LEFT JOIN "CATEGORIA" c    ON c.id_categoria = p.id_categoria
      LEFT JOIN "DETALLES_PRODUCTO" d ON d.id_producto = p.id_producto
      JOIN "CALIFICACION_PRODUCTO" cp ON cp.id_producto = p.id_producto
      WHERE p.activo = TRUE
      GROUP BY p.id_producto, p.nombre, a.nombre, c.nombre, d.precio
    ),
    ranked AS (
      SELECT
        *,
        ROW_NUMBER()  OVER (ORDER BY n_calificaciones DESC, calif_prom DESC, id_producto ASC) AS top,
        COUNT(*)      OVER () AS total
      FROM agg
    )
    SELECT id_producto, top, nombre, autor, categoria, precio, n_calificaciones, calif_prom, total
    FROM ranked
    WHERE top > %s AND top <= %s
    ORDER BY top;
    """
    with connection.cursor() as cur:
        cur.execute(sql, [lo, hi])
        rows = cur.fetchall()

    filas = [{
        "id": r[0],
        "top": int(r[1]),
        "nombre": r[2],
        "autor": r[3],
        "categoria": r[4],
        "precio": r[5],
        "n_calificaciones": int(r[6]),
        "calif_prom": r[7],
    } for r in rows]

    total = int(rows[0][-1]) if rows else 0
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    return filas, total_pages
