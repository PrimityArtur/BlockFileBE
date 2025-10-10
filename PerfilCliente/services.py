
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any

from django.db import transaction

from . import repository as repo
from core.utils import PER_PAGE

def obtener_perfil_cliente(
        usuario_id: int
) -> Optional[Dict[str, Any]]:
    return repo.perfil_cliente(usuario_id)

def validar_usuario(
        usuario_id: int,
        nombre_usuario: str,
        correo: str
) -> None:
    if repo.existe_nombre_usuario(nombre_usuario, usuario_id):
        raise ValueError("El nombre de usuario ya está en uso.")
    if repo.existe_correo(correo, usuario_id):
        raise ValueError("El correo ya está en uso.")

def actualizar_perfil_cliente(
        usuario_id: int,
        nombre_usuario: str,
        correo: str,
        contrasena: Optional[str]
) -> None:
    repo.actualizar_usuario(usuario_id, nombre_usuario, correo, contrasena or None)