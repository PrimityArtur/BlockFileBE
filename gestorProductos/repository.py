from decimal import Decimal
from typing import Optional, Tuple, List, Dict

from django.db import transaction, connection
from django.db.models import Avg, Prefetch

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
        page: int = 1,
        per_page: int = PER_PAGE,
        f_id: Optional[int] = None,
        f_nombre: Optional[str] = None,
        f_autor: Optional[str] = None,
        f_categoria: Optional[str] = None,
) -> Tuple[List[dict], int]:
    page = max(1, int(page or 1))
    per_page = max(1, int(per_page or PER_PAGE))
    offset = (page - 1) * per_page

    where, params = ['p.activo = TRUE'], []
    if f_id:        where += ['p.id_producto = %s'];           params += [f_id]
    if f_nombre:    where += ['p.nombre ILIKE %s'];             params += [f'%{f_nombre}%']
    if f_autor:     where += ['a.nombre ILIKE %s'];             params += [f'%{f_autor}%']
    if f_categoria: where += ['c.nombre ILIKE %s'];             params += [f'%{f_categoria}%']

    sql = f"""
        SELECT
            p.id_producto                                   AS id,
            p.nombre                                        AS nombre,
            COALESCE(a.nombre, '')                          AS autor,
            COALESCE(c.nombre, '')                          AS categoria,
            ROUND(AVG(cp.calificacion)::numeric, 1)         AS promedio,
            COUNT(*) OVER()                                 AS total
        FROM "PRODUCTO" p
        LEFT JOIN "AUTOR"               a  ON a.id_autor     = p.id_autor
        LEFT JOIN "CATEGORIA"           c  ON c.id_categoria = p.id_categoria
        LEFT JOIN "CALIFICACION_PRODUCTO" cp ON cp.id_producto = p.id_producto
        WHERE {" AND ".join(where)}
        GROUP BY p.id_producto, p.nombre, a.nombre, c.nombre
        ORDER BY p.id_producto ASC
        OFFSET %s LIMIT %s;
        """

    with connection.cursor() as cur:
        cur.execute(sql, params + [offset, per_page])
        rows = cur.fetchall()

    total = int(rows[0][-1]) if rows else 0
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1

    filas = [
        {
            "id": rid,
            "nombre": nombre,
            "autor": autor,
            "categoria": categoria,
            "promedio": float(prom) if prom is not None else None,
        }
        for rid, nombre, autor, categoria, prom, _ in rows
    ]
    return filas, total_pages


def obtener_producto_detalle(id_producto: int) -> Optional[dict]:
    sql_prod = '''
        SELECT
            p.id_producto,
            p.nombre,
            p.fecha,
            p.activo,
            (p.archivo IS NOT NULL AND octet_length(p.archivo) > 0) AS tiene_archivo,
            a.id_autor,
            a.nombre          AS autor_nombre,
            c.id_categoria,
            c.nombre          AS categoria_nombre,
            d.precio,
            d.version,
            d.descripcion,
            ROUND(AVG(cp.calificacion)::numeric, 1) AS calificacion
        FROM "PRODUCTO" p
        LEFT JOIN "AUTOR"     a ON a.id_autor     = p.id_autor
        LEFT JOIN "CATEGORIA" c ON c.id_categoria = p.id_categoria
        LEFT JOIN "DETALLES_PRODUCTO" d ON d.id_producto = p.id_producto
        LEFT JOIN "CALIFICACION_PRODUCTO" cp ON cp.id_producto = p.id_producto
        WHERE p.id_producto = %s
        GROUP BY
            p.id_producto, p.nombre, p.fecha, p.activo, tiene_archivo,
            a.id_autor, a.nombre, c.id_categoria, c.nombre,
            d.precio, d.version, d.descripcion
        LIMIT 1;
    '''

    # imagenes
    sql_imgs = '''
        SELECT id_imagen_producto, orden
        FROM "IMAGEN_PRODUCTO"
        WHERE id_producto = %s
        ORDER BY orden ASC;
    '''

    with connection.cursor() as cur:
        cur.execute(sql_prod, [id_producto])
        row = cur.fetchone()
        if not row:
            return None

        (pid, nombre, fecha, activo, tiene_archivo,
         autor_id, autor_nombre, cat_id, cat_nombre,
         precio, version, descripcion, calif) = row

        cur.execute(sql_imgs, [pid])
        imgs_rows = cur.fetchall()

    imagenes: List[Dict[str, int]] = [
        {"id": iid, "orden": orden} for (iid, orden) in imgs_rows
    ]

    return {
        "id": pid,
        "nombre": nombre,
        "fecha": fecha.isoformat() if fecha else None,
        "calificacion": float(calif) if calif is not None else None,
        "descripcion": descripcion or "",
        "version": version or "",
        "precio": str(precio) if precio is not None else "0.00",
        "categoria_id": cat_id,
        "categoria": cat_nombre or "",
        "autor_id": autor_id,
        "autor": autor_nombre or "",
        "imagenes": imagenes,
        "activo": bool(activo),
        "tiene_archivo": bool(tiene_archivo),
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
    with connection.cursor() as cur:
        if id_producto:
            # UPDATE producto
            cur.execute(
                '''
                UPDATE "PRODUCTO"
                SET nombre = %s, id_autor = %s, id_categoria = %s, activo = %s
                WHERE id_producto=%s
                RETURNING id_producto;
                ''',
                [nombre, id_autor, id_categoria, activo, id_producto],
            )
            pid = cur.fetchone()[0]
        else:
            # INSERT producto
            cur.execute(
                '''
                INSERT INTO "PRODUCTO"(nombre, id_autor, id_categoria, activo, archivo, fecha)
                VALUES (%s, %s, %s, %s, %s, NOW())
                RETURNING id_producto;
                ''',
                [nombre, id_autor, id_categoria, activo, b""],
            )
            pid = cur.fetchone()[0]

        # INSERT detalles
        cur.execute(
            '''
            INSERT INTO "DETALLES_PRODUCTO"(id_producto, descripcion, version, precio)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id_producto) DO UPDATE
              SET descripcion = EXCLUDED.descripcion,
                  version     = EXCLUDED.version,
                  precio      = EXCLUDED.precio;
            ''',
            [pid, descripcion, version, precio],
        )

    return pid

@transaction.atomic
def agregar_imagen_binaria(id_producto: int, *, contenido: bytes, orden: Optional[int] = None) -> int:
    with connection.cursor() as cur:
        if orden is None:
            cur.execute('SELECT COALESCE(MAX(orden), 0) + 1 FROM "IMAGEN_PRODUCTO" WHERE id_producto = %s;', [id_producto])
            orden = cur.fetchone()[0]

        cur.execute(
            '''
            INSERT INTO "IMAGEN_PRODUCTO"(id_producto, orden, archivo)
            VALUES (%s, %s, %s)
            RETURNING id_imagen_producto;
            ''',
            [id_producto, orden, contenido],
        )
        img_id = cur.fetchone()[0]

    return img_id

@transaction.atomic
def borrar_imagen(id_imagen: int) -> None:
    with connection.cursor() as cur:
        cur.execute('DELETE FROM "IMAGEN_PRODUCTO" WHERE id_imagen_producto = %s;', [id_imagen])


@transaction.atomic
def reordenar_imagen(id_imagen: int, nuevo_orden: int) -> None:
    with connection.cursor() as cur:
        cur.execute(
            '''
            UPDATE "IMAGEN_PRODUCTO"
            SET orden = %s
            WHERE id_imagen_producto = %s;
            ''',
            [nuevo_orden, id_imagen],
        )


@transaction.atomic
def eliminar_producto(id_producto: int) -> None:
    with connection.cursor() as cur:
        cur.execute(
            '''
            UPDATE "PRODUCTO"
            SET activo = FALSE
            WHERE id_producto = %s;
            ''',
            [id_producto],
        )


def actualizar_archivo_producto(
        id_producto: int,
        archivo_bytes: bytes
) -> None:
    sql = 'UPDATE "PRODUCTO" SET archivo = %s WHERE id_producto = %s'
    with connection.cursor() as cur:
        cur.execute(sql, [archivo_bytes, id_producto])


def archivo_producto(
        producto_id: int
) -> Optional[Tuple[str, bytes]]:
    sql = """
    SELECT p.nombre, p.archivo
    FROM "PRODUCTO" p
    WHERE p.id_producto = %s AND p.activo = TRUE
    """
    with connection.cursor() as cur:
        cur.execute(sql, [producto_id])
        row = cur.fetchone()
    if not row:
        return None
    nombre, archivo = row
    return (str(nombre), bytes(archivo))
