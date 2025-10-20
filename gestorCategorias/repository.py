from typing import Optional, Tuple, List

from django.db import transaction, connection

from core.models import Categoria
from core.utils import PER_PAGE


def listar_pagina(
        *,
        page: int = 1,
        per_page: int = PER_PAGE,
        f_id: Optional[int] = None,
        f_nombre: Optional[str] = None,
        f_descripcion: Optional[str] = None,
) -> Tuple[List[dict], int]:
    page = max(1, int(page or 1))
    per_page = max(1, int(per_page or PER_PAGE))
    offset = (page - 1) * per_page

    where, params = ['TRUE'], []
    if f_id:
        where.append('c.id_categoria = %s');
        params.append(f_id)
    if f_nombre:
        where.append('c.nombre ILIKE %s');
        params.append(f'%{f_nombre}%')
    if f_descripcion:
        where.append('c.descripcion ILIKE %s');
        params.append(f'%{f_descripcion}%')

    sql = f"""
    WITH base AS (
        SELECT 
            c.id_categoria,
            c.nombre,
            COALESCE(c.descripcion, '') AS descripcion,
            COUNT(*) OVER() AS total,
            ROW_NUMBER() OVER (ORDER BY c.id_categoria ASC) AS rn
        FROM "CATEGORIA" c
        WHERE {' AND '.join(where)}
    )
    SELECT id_categoria, nombre, descripcion, total
    FROM base
    WHERE rn > %s AND rn <= %s
    ORDER BY id_categoria ASC;
    """

    lo, hi = offset, offset + per_page

    with connection.cursor() as cur:
        cur.execute(sql, params + [lo, hi])
        rows = cur.fetchall()

    total = int(rows[0][-1]) if rows else 0
    total_pages = max(1, (total + per_page - 1) // per_page)

    filas = [
        {"id": r[0], "nombre": r[1], "descripcion": r[2]}
        for r in rows
    ]
    return filas, total_pages


def obtener_categoria_detalle(id_categoria: int) -> Optional[dict]:
    sql = '''
    SELECT 
        id_categoria,
        nombre,
        fecha,
        descripcion
    FROM "CATEGORIA"
    WHERE id_categoria = %s;
    '''
    with connection.cursor() as cur:
        cur.execute(sql, [id_categoria])
        row = cur.fetchone()

    if not row:
        return None

    id_categoria, nombre, fecha, descripcion = row
    return {
        "id": id_categoria,
        "nombre": nombre,
        "fecha": fecha.isoformat() if fecha else None,
        "descripcion": descripcion,
    }


@transaction.atomic
def crear_actualizar_categoria(
        *,
        id_categoria: Optional[int],
        nombre: str,
        descripcion: str,
) -> int:
    with connection.cursor() as cur:
        if id_categoria:
            cur.execute(
                '''
                UPDATE "CATEGORIA"
                SET nombre = %s, descripcion = %s
                WHERE id_categoria = %s;
                ''',
                [nombre, descripcion, id_categoria],
            )
            return id_categoria
        else:
            cur.execute(
                '''
                INSERT INTO "CATEGORIA"(nombre, descripcion)
                VALUES (%s, %s)
                RETURNING id_categoria;
                ''',
                [nombre, descripcion],
            )
            new_id = cur.fetchone()[0]
            return new_id


@transaction.atomic
def eliminar_categoria(id_categoria: int) -> None:
    with connection.cursor() as cur:
        cur.execute(
            '''
            DELETE FROM "CATEGORIA"
            WHERE id_categoria = %s;
            ''',
            [id_categoria],
        )