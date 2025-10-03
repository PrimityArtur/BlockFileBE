
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List, Tuple

from django.db import transaction

from . import repository as repo
from core.utils import PER_PAGE

def listar_pagina(*, page:int, per_page:int=PER_PAGE, **filtros) -> Tuple[list,int]:
    return repo.listar_pagina(page=page, per_page=per_page, **filtros)

def obtener_detalle(id_categoria:int) -> Optional[dict]:
    return repo.obtener_categoria_detalle(id_categoria)

def guardar_categoria(
    *,
    id: Optional[int],
    nombre: str,
    descripcion: str,
) -> int:
    return repo.crear_actualizar_categoria(
        id_categoria=id,
        nombre=nombre,
        descripcion=descripcion,
    )

def eliminar_categoria(*, id_categoria:int) -> None:
    repo.eliminar_categoria(id_categoria)


