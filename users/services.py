from django.db import transaction

from .models import Usuario, Cliente, Administrador
from . import repository as repo

class DomainError(Exception):
    pass


def autenticar_usuario(*, nombre: str, contrasena: str) -> dict:
    # Verifica credenciales y determina el tipo de usuario.

    usuario = repo.get_usuario(nombre=nombre)
    if not usuario or usuario.contrasena != contrasena:
        raise DomainError("Usuario o contraseña inválidos.")

    if hasattr(usuario, "administrador"):
        tipo = "administrador"
    elif hasattr(usuario, "cliente"):
        tipo = "cliente"
    else:
        tipo = "desconocido"

    return {"usuario": usuario, "tipo": tipo} # "tipo": "cliente" "administrador" "desconocido"


@transaction.atomic
def registrar_usuario_y_cliente(*, nombre: str, correo: str, contrasena: str) -> Usuario:
    # - Verifica duplicados de nombre/correo
    # - Crea Usuario y Cliente con repo.CrearUsuario

    if repo.usuario_existe(nombre=nombre):
        raise DomainError("El nombre de usuario ya existe.")
    if repo.usuario_existe(correo=correo):
        raise DomainError("El correo ya está registrado.")

    usuario = repo.crear_usuario(
        nombre=nombre,
        correo=correo,
        contrasena=contrasena,
    )
    repo.get_create_cliente(usuario=usuario)
    return usuario


@transaction.atomic
def actualizar_datos_administrador(*, usuario_id: int, nombre: str, contrasena: str, correo: str) -> Usuario:
    usuario = repo.get_usuario(id=usuario_id)
    if not usuario:
        raise DomainError("Administrador no encontrado.")
    if not Administrador.objects.filter(pk=usuario_id).exists():
        raise DomainError("No tienes permisos de administrador.")

    if repo.usuario_existe(exclude_id=usuario_id, nombre=nombre):
        raise DomainError("El nombre de usuario ya existe.")
    if repo.usuario_existe(exclude_id=usuario_id, correo=correo):
        raise DomainError("El correo ya está registrado.")

    # update usuario
    usuario = repo.actualizar_usuario(usuario_id=usuario_id, nombre=nombre, correo=correo, contrasena=contrasena)
    return usuario