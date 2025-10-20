
from typing import Optional, Tuple, List, Iterable, Dict, Any
from decimal import Decimal
from django.db.models import Q, Avg, Prefetch
from django.core.paginator import Paginator
from django.db import transaction, connection

from core.models import (
    Producto, Usuario, Cliente, ImagenProducto, DetallesProducto
)
from core.utils import PER_PAGE


def perfil_cliente(
        usuario_id: int
) -> Optional[Dict[str, Any]]:
    sql = """
    WITH compras AS (
      SELECT COUNT(*)::bigint AS n
      FROM "COMPRA_PRODUCTO"
      WHERE id_usuario = %s
    )
    SELECT
      u.id_usuario,
      u.nombre_usuario,
      u.correo,
      u.contrasena,
      cl.saldo,
      (SELECT n FROM compras) AS num_compras
    FROM "USUARIO" u
    JOIN "CLIENTE" cl ON cl.id_usuario = u.id_usuario
    WHERE u.id_usuario = %s
    """
    with connection.cursor() as cur:
        cur.execute(sql, [usuario_id, usuario_id])
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id_usuario": row[0],
        "nombre_usuario": row[1],
        "correo": row[2],
        "contrasena": row[3],
        "saldo": row[4],
        "num_compras": int(row[5] or 0),
    }

def existe_nombre_usuario(nombre_usuario: str, excluir_id: int) -> bool:
    sql = 'SELECT EXISTS(SELECT 1 FROM "USUARIO" WHERE nombre_usuario = %s AND id_usuario <> %s)'
    with connection.cursor() as cur:
        cur.execute(sql, [nombre_usuario, excluir_id])
        (exists,) = cur.fetchone()
    return bool(exists)

def existe_correo(correo: str, excluir_id: int) -> bool:
    sql = 'SELECT EXISTS(SELECT 1 FROM "USUARIO" WHERE correo = %s AND id_usuario <> %s)'
    with connection.cursor() as cur:
        cur.execute(sql, [correo, excluir_id])
        (exists,) = cur.fetchone()
    return bool(exists)

def actualizar_usuario(usuario_id: int, nombre_usuario: str, correo: str, contrasena: Optional[str]) -> None:
    if contrasena:
        sql = 'UPDATE "USUARIO" SET nombre_usuario = %s, correo = %s, contrasena = %s WHERE id_usuario = %s'
        params = [nombre_usuario, correo, contrasena, usuario_id]
    else:
        sql = 'UPDATE "USUARIO" SET nombre_usuario = %s, correo = %s WHERE id_usuario = %s'
        params = [nombre_usuario, correo, usuario_id]
    with connection.cursor() as cur:
        cur.execute(sql, params)


def compras_cliente(
        usuario_id: int,
        page: int,
        per_page: int
) -> Tuple[List[Dict[str, Any]], int]:
    page     = max(1, int(page or 1))
    per_page = max(1, int(per_page or 10))
    lo, hi   = (page - 1) * per_page, (page - 1) * per_page + per_page

    sql = """
    WITH base AS (
      SELECT
        p.id_producto                                     AS id,
        p.nombre                                          AS nombre,
        COALESCE(a.nombre,'')                             AS autor,
        d.precio                                          AS precio,
        ( SELECT ip.id_imagen_producto
          FROM "IMAGEN_PRODUCTO" ip
          WHERE ip.id_producto = p.id_producto
          ORDER BY ip.orden ASC
          LIMIT 1 )                                       AS imagen_1_id,
        ( SELECT ROUND(AVG(cp.calificacion)::numeric, 2)
          FROM "CALIFICACION_PRODUCTO" cp
          WHERE cp.id_producto = p.id_producto )          AS calif_prom,
        ( SELECT COUNT(*)::bigint
          FROM "COMPRA_PRODUCTO" ctot
          WHERE ctot.id_producto = p.id_producto )        AS compras,
        c.fecha                                           AS fecha_compra
      FROM "COMPRA_PRODUCTO" c
      JOIN "PRODUCTO" p  ON p.id_producto = c.id_producto
      LEFT JOIN "AUTOR" a ON a.id_autor = p.id_autor
      LEFT JOIN "DETALLES_PRODUCTO" d ON d.id_producto = p.id_producto
      WHERE c.id_usuario = %s
    ),
    ranked AS (
      SELECT *,
             ROW_NUMBER() OVER (ORDER BY fecha_compra DESC ) AS rn,
             COUNT(*)    OVER ()                 AS total
      FROM base
    )
    SELECT id, nombre, autor, precio, imagen_1_id, calif_prom, compras, total
    FROM ranked
    WHERE rn > %s AND rn <= %s
    ORDER BY rn;
    """
    with connection.cursor() as cur:
        cur.execute(sql, [usuario_id, lo, hi])
        rows = cur.fetchall()

    total = int(rows[0][-1]) if rows else 0
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1

    filas = [{
        "id": r[0],
        "nombre": r[1],
        "autor": r[2],
        "precio": float(r[3]) if r[3] is not None else None,
        "imagen_1_id": r[4],
        "calificacion_promedio": float(r[5]) if r[5] is not None else None,
        "compras": int(r[6]),
    } for r in rows]
    return filas, total_pages