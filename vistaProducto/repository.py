from typing import Optional, Tuple, List, Dict, Any, Literal
from django.db import connection

def obtener_detalle_producto(
        producto_id: int,
        cliente_id: Optional[int]
) -> Dict[str, Any]:
    sql = """
    SELECT
      p.id_producto                                         AS id,
      p.nombre                                              AS nombre,
      COALESCE(a.nombre, '')                                AS autor,
      COALESCE(c.nombre, '')                                AS categoria,
      p.fecha                                               AS fecha_publicacion,
      d.descripcion                                         AS descripcion,
      d.precio                                              AS precio,
      d.version                                             AS version,
      -- imágenes 
      (
        SELECT ARRAY_AGG(ip.id_imagen_producto ORDER BY ip.orden ASC)
        FROM "IMAGEN_PRODUCTO" ip
        WHERE ip.id_producto = p.id_producto
      )                                                     AS imagen_ids,
      -- calificación
      (
        SELECT ROUND(AVG(cp.calificacion)::numeric, 1)
        FROM "CALIFICACION_PRODUCTO" cp
        WHERE cp.id_producto = p.id_producto
      )                                                     AS calificacion_promedio,
      -- compras
      (
        SELECT COUNT(*)::bigint
        FROM "COMPRA_PRODUCTO" co
        WHERE co.id_producto = p.id_producto
      )                                                     AS compras,
      -- saldo del cliente
      (
        SELECT cl.saldo
        FROM "CLIENTE" cl
        WHERE cl.id_usuario = %s
      )                                                     AS saldo_cliente,
      -- el cliente compro el producto
      EXISTS(
        SELECT 1
        FROM "COMPRA_PRODUCTO" co2
        WHERE co2.id_producto = p.id_producto AND co2.id_usuario = %s
      )                                                     AS cliente_compro
    FROM "PRODUCTO" p
    LEFT JOIN "AUTOR"      a ON a.id_autor     = p.id_autor
    LEFT JOIN "CATEGORIA"  c ON c.id_categoria = p.id_categoria
    LEFT JOIN "DETALLES_PRODUCTO" d ON d.id_producto = p.id_producto
    WHERE p.id_producto = %s AND p.activo = TRUE
    """
    params = [cliente_id, cliente_id, producto_id]

    with connection.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()

    if not row:
        return {}

    (
        pid, nombre, autor, categoria, fecha_pub,
        descripcion, precio, version, imagen_ids,
        calif_prom, compras, saldo_cliente, cliente_compro
    ) = row

    return {
        "id": pid,
        "nombre": nombre,
        "autor": autor,
        "categoria": categoria,
        "fecha_publicacion": fecha_pub,
        "descripcion": descripcion,
        "precio": float(precio) if precio is not None else None,
        "version": version,
        "imagen_ids": list(imagen_ids or []),
        "calificacion_promedio": float(calif_prom) if calif_prom is not None else None,
        "compras": int(compras or 0),
        "saldo_cliente": float(saldo_cliente) if saldo_cliente is not None else None,
        "cliente_compro": bool(cliente_compro),
    }


def listar_comentarios_producto(
        producto_id: int
) -> List[Dict[str, Any]]:
    sql = """
    SELECT
      u.nombre_usuario                                      AS cliente,
      cal.calificacion                                      AS calificacion,
      cm.fecha                                              AS fecha,
      cm.descripcion                                        AS descripcion
    FROM "COMENTARIO_PRODUCTO" cm
    JOIN "USUARIO" u
      ON u.id_usuario = cm.id_usuario
    LEFT JOIN "CALIFICACION_PRODUCTO" cal
      ON cal.id_producto = cm.id_producto AND cal.id_usuario = cm.id_usuario
    WHERE cm.id_producto = %s
    ORDER BY cm.fecha DESC, cm.id_comentario_producto DESC
    """
    with connection.cursor() as cur:
        cur.execute(sql, [producto_id])
        rows = cur.fetchall()

    return [
        {
            "cliente": r[0],
            "calificacion": int(r[1]) if r[1] is not None else None,
            "fecha": r[2],
            "descripcion": r[3],
        }
        for r in rows
    ]

def registrar_compra(
        producto_id: int,
        usuario_id: int
) -> Literal["created","exists","invalid"]:
    with connection.cursor() as cur:
        cur.execute(
            'SELECT 1 FROM "PRODUCTO" WHERE id_producto=%s AND activo=TRUE', [producto_id])
        if cur.fetchone() is None:
            return "invalid"

        cur.execute(
            '''
            INSERT INTO "COMPRA_PRODUCTO"(id_producto, id_usuario)
            VALUES (%s, %s)
            ON CONFLICT (id_producto, id_usuario) DO NOTHING
            ''',
            [producto_id, usuario_id],
        )
        return "created" if cur.rowcount > 0 else "exists"


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



def calificar_producto(
        producto_id: int,
        usuario_id: int,
        calificacion: int
) -> None:
    sql = """
    INSERT INTO "CALIFICACION_PRODUCTO" (id_usuario, id_producto, calificacion, fecha)
    VALUES (%s, %s, %s, NOW())
    ON CONFLICT (id_usuario, id_producto)
    DO UPDATE SET calificacion = EXCLUDED.calificacion,
                  fecha = NOW();
    """
    with connection.cursor() as cur:
        cur.execute(sql, [usuario_id, producto_id, calificacion])


def comentar_producto(
        producto_id: int,
        usuario_id: int,
        descripcion: str
) -> None:
    sql = """
    INSERT INTO "COMENTARIO_PRODUCTO" (id_producto, id_usuario, descripcion, fecha)
    VALUES (%s, %s, %s, NOW());
    """
    with connection.cursor() as cur:
        cur.execute(sql, [producto_id, usuario_id, descripcion])
