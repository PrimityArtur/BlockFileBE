
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List, Tuple

from django.db import transaction

from . import repository as repo
from core.utils import PER_PAGE

def listar_pagina(*, page:int, per_page:int=PER_PAGE, **filtros) -> Tuple[list,int]:
    return repo.listar_pagina(page=page, per_page=per_page, **filtros)

def obtener_detalle(id_usuario:int) -> Optional[dict]:
    return repo.obtener_usuario_detalle(id_usuario)

def guardar_usuario(
    *,
    id: Optional[int],
    saldo: Decimal,
) -> int:
    return repo.actualizar_usuario(
        id_usuario=id,
        saldo=saldo,
    )


def eliminar_usuario(*, id_usuario:int) -> None:
    repo.eliminar_usuario(id_usuario)


