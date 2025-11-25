from typing import Optional

from django.db import connection

from core.models import Usuario, Cliente


#  Lectura

def get_usuario(
        *,
        id: Optional[int] = None,
        nombre: Optional[str] = None,
        correo: Optional[str] = None
) -> Optional[Usuario]:
    where, params = [], []
    if id is not None:      where += ['id_usuario=%s'];       params += [id]
    if nombre is not None:  where += ['nombre_usuario=%s'];   params += [nombre]
    if correo is not None:  where += ['correo=%s']; params += [correo]

    if not where:
        return None

    sql = f'SELECT id_usuario, correo, nombre_usuario, contrasena FROM "USUARIO" {"WHERE " + " AND ".join(where) if where else ""} LIMIT 1;'
    with connection.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()

    return Usuario(id_usuario=row[0], correo=row[1], nombre_usuario=row[2], contrasena=row[3]) if row else None


def usuario_existe(*, nombre: Optional[str] = None,
                   correo: Optional[str] = None,
                   exclude_id: Optional[int] = None) -> bool:
    cond, params = [], []
    if nombre:    cond += ['nombre_usuario=%s'];          params += [nombre]
    if correo:    cond += ['LOWER(correo)=LOWER(%s)'];    params += [correo]
    if not cond:  return False

    where = ' OR '.join(cond)
    if exclude_id: where = f'({where}) AND id_usuario<>%s'; params += [exclude_id]

    sql = f'SELECT 1 FROM "USUARIO" WHERE {where} LIMIT 1;'
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() is not None


def crear_usuario(*, nombre: str, correo: str, contrasena: str) -> Usuario:
    sql = '''
        INSERT INTO "USUARIO"(nombre_usuario, correo, contrasena)
        VALUES (%s, %s, %s)
        RETURNING id_usuario, correo, nombre_usuario, contrasena;
    '''
    with connection.cursor() as cur:
        cur.execute(sql, [nombre, correo, contrasena])
        id, correo, nom, contr = cur.fetchone()

    return Usuario(id_usuario=id, correo=correo, nombre_usuario=nom, contrasena=contr)


def get_create_cliente(*, usuario: Usuario) -> Cliente:
    sql = '''
        INSERT INTO "CLIENTE"(id_usuario, excliente, fecha_creacion, saldo)
        VALUES (%s, FALSE, NOW(), 0)
        ON CONFLICT (id_usuario) DO NOTHING
        RETURNING id_usuario, excliente, fecha_creacion, saldo;
    '''
    with connection.cursor() as cur:
        cur.execute(sql, [usuario.id_usuario])
        row = cur.fetchone()

        if not row:
            cur.execute('SELECT id_usuario, excliente, fecha_creacion, saldo FROM "CLIENTE" WHERE id_usuario=%s;',
                        [usuario.id_usuario])
            row = cur.fetchone()

    id, excliente, fecha, saldo = row
    return Cliente(usuario_id=id, excliente=excliente, fecha_creacion=fecha, saldo=saldo)


def actualizar_usuario(
        *,
        usuario_id: int,
        nombre: Optional[str]=None,
        contrasena: Optional[str]=None,
        correo: Optional[str]=None
) -> Usuario:
    sets, params = [], []
    if nombre:     sets += ['nombre_usuario=%s'];  params += [nombre]
    if contrasena: sets += ['contrasena=%s'];      params += [contrasena]
    if correo:     sets += ['correo=%s'];          params += [correo]

    if sets:
        sql = f'UPDATE "USUARIO" SET {", ".join(sets)} WHERE id_usuario=%s RETURNING id_usuario, correo, nombre_usuario, contrasena;'
        params.append(usuario_id)
    else:
        sql = 'SELECT id_usuario, correo, nombre_usuario, contrasena FROM "USUARIO" WHERE id_usuario=%s;'
        params = [usuario_id]

    with connection.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()

    id, corr, nom, contr = row
    return Usuario(id_usuario=id, correo= corr, nombre_usuario=nom, contrasena=contr)