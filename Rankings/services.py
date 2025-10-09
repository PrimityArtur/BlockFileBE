
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List, Tuple

from django.db import transaction

from . import repository as repo
from core.utils import PER_PAGE

def listar_pagina(*, page:int, per_page:int=PER_PAGE, **filtros) -> Tuple[list,int]:
    return repo.listar_pagina(page=page, per_page=per_page, **filtros)
