from typing import Optional, List, Tuple, Literal
import magic
import mimetypes

from django.db import transaction

from . import repository as repo

def descargar_producto(producto_id: int) -> Tuple[str, bytes, str]:
    data = repo.archivo_producto(producto_id)
    nombre, contenido = data

    mime = magic.Magic(mime=True).from_buffer(contenido[:4096]) or "application/octet-stream"
    ext = mimetypes.guess_extension(mime) or ""
    base = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in nombre).strip() or "archivo"

    filename = f"{base}{ext}"
    return filename, contenido, mime

def calificar_producto(producto_id: int, usuario_id: int, calificacion: int) -> None:
    repo.calificar_producto(producto_id, usuario_id, calificacion)


def comentar_producto(producto_id: int, usuario_id: int, descripcion: str) -> None:
    repo.comentar_producto(producto_id, usuario_id, descripcion)

# ============ COMPRAR PRODUCTO
def validar_y_registrar_compra(
    producto_id: int, usuario_id: int
) -> Literal["created","exists","invalid","insufficient","no_cliente"]:
    precio = repo.get_producto_precio(producto_id)
    if precio is None:
        return "invalid"

    # Transacción y bloqueo del saldo del cliente
    with transaction.atomic():
        saldo = repo.get_cliente_saldo_for_update(usuario_id)
        if saldo is None:
            return "no_cliente"

        if repo.existe_compra(producto_id, usuario_id):
            return "exists"

        if saldo < precio:
            return "insufficient"

        # Debita y registra
        ok = repo.reducir_saldo(usuario_id, precio)
        if not ok:
            # alguien pudo debitar en otra operación concurrente
            return "insufficient"

        repo.insert_compra(producto_id, usuario_id)
        return "created"