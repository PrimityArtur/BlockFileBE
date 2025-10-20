
from typing import Optional, Tuple, List, Iterable
from decimal import Decimal
from django.db.models import Q, Avg, Prefetch
from django.core.paginator import Paginator
from django.db import transaction, connection

from core.utils import PER_PAGE

def listar_pagina(
    *,
    page: int = 1,
    per_page: int = PER_PAGE,
    f_id: Optional[int] = None,
    f_nombre: Optional[str] = None,
    f_saldo: Optional[Decimal] = None,
) -> Tuple[List[dict], int]:
    page     = max(1, int(page or 1))
    per_page = max(1, int(per_page or PER_PAGE))
    offset   = (page - 1) * per_page

    where, params = ['c.excliente = FALSE'], []
    if f_id:     where += ['u.id_usuario = %s'];           params += [f_id]
    if f_nombre: where += ['u.nombre_usuario ILIKE %s'];    params += [f'%{f_nombre}%']
    if f_saldo is not None: where += ['c.saldo = %s'];     params += [f_saldo]

    sql = f'''
    SELECT
      u.id_usuario,
      u.nombre_usuario,
      c.saldo,
      COUNT(*) OVER() AS total
    FROM "USUARIO" u
    JOIN "CLIENTE" c ON c.id_usuario = u.id_usuario
    {'WHERE ' + ' AND '.join(where) if where else ''}
    ORDER BY u.id_usuario ASC
    OFFSET %s LIMIT %s;
    '''

    with connection.cursor() as cur:
        cur.execute(sql, params + [offset, per_page])
        rows = cur.fetchall()

    total = int(rows[0][3]) if rows else 0
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1

    filas = [
        {"id": r[0], "nombre": r[1], "saldo": r[2]}
        for r in rows
    ]
    return filas, total_pages

def obtener_usuario_detalle(id_usuario: int) -> Optional[dict]:
    sql = '''
        SELECT
            u.id_usuario,
            u.nombre_usuario,
            u.correo,
            c.fecha_creacion,
            c.saldo
        FROM "USUARIO" u
        JOIN "CLIENTE" c ON c.id_usuario = u.id_usuario
        WHERE u.id_usuario = %s
        LIMIT 1;
    '''
    with connection.cursor() as cur:
        cur.execute(sql, [id_usuario])
        row = cur.fetchone()

    if not row:
        return None

    uid, nombre, correo, fecha, saldo = row
    return {
        "id": uid,
        "nombre": nombre,
        "fecha": fecha.isoformat() if fecha else None,
        "correo": correo,
        "saldo": saldo,
    }


@transaction.atomic
def actualizar_usuario(
    *,
    id_usuario: Optional[int],
    saldo: Decimal,
) -> int:
    with connection.cursor() as cur:
        cur.execute('UPDATE "CLIENTE" SET saldo = %s WHERE id_usuario= %s;', [saldo, id_usuario])

    return id_usuario

@transaction.atomic
def eliminar_usuario(id_usuario:int) -> None:
    with connection.cursor() as cur:
        cur.execute('UPDATE "CLIENTE" SET excliente=TRUE WHERE id_usuario=%s;', [id_usuario])