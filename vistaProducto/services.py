from typing import Optional, List, Tuple
import magic
import mimetypes

from . import repository as repo

def descargar_producto(producto_id: int) -> Tuple[str, bytes]:
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
