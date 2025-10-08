import mimetypes
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List, Tuple

from django.db import transaction
import magic

from . import repository as repo
from core.utils import PER_PAGE

def listar_pagina(*, page:int, per_page:int=PER_PAGE, **filtros) -> Tuple[list,int]:
    return repo.listar_pagina(page=page, per_page=per_page, **filtros)

def obtener_detalle(id_producto:int) -> Optional[dict]:
    return repo.obtener_producto_detalle(id_producto)

def guardar_producto(
    *,
    id: Optional[int],
    nombre: str,
    descripcion: str,
    version: str,
    precio: str,
    id_autor: Optional[int],
    id_categoria: Optional[int],
    activo: bool,
) -> int:
    return repo.crear_actualizar_producto(
        id_producto=id,
        nombre=nombre,
        descripcion=descripcion,
        version=version,
        precio=Decimal(precio),
        id_autor=id_autor,
        id_categoria=id_categoria,
        activo=activo,
    )

def agregar_imagen(*, id_producto:int, contenido:bytes, orden:Optional[int]=None) -> int:
    return repo.agregar_imagen_binaria(id_producto, contenido=contenido, orden=orden)

def borrar_imagen(*, id_imagen:int) -> None:
    repo.borrar_imagen(id_imagen)

def reordenar_imagen(*, id_imagen:int, nuevo_orden:int) -> None:
    repo.reordenar_imagen(id_imagen, nuevo_orden)

def eliminar_producto(*, id_producto:int) -> None:
    repo.eliminar_producto(id_producto)

def subir_archivo_producto_srv(id_producto: int, contenido: bytes) -> None:
    repo.actualizar_archivo_producto(id_producto, contenido)


def descargar_producto(producto_id: int) -> Tuple[str, bytes, str]:
    data = repo.archivo_producto(producto_id)
    nombre, contenido = data

    mime = magic.Magic(mime=True).from_buffer(contenido[:4096]) or "application/octet-stream"
    ext = mimetypes.guess_extension(mime) or ""
    base = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in nombre).strip() or "archivo"

    filename = f"{base}{ext}"
    return filename, contenido, mime