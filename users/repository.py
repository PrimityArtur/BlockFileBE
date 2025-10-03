from django.db import connection
from core.models import Usuario, Cliente
from typing import Optional
from django.db.models import Q

#  Lectura

def get_usuario(*, id: Optional[int] = None,
                nombre: Optional[str] = None,
                correo: Optional[str] = None) -> Optional[Usuario]:
    qs = Usuario.objects.all()
    if id is not None:
        qs = qs.filter(pk=id)
    if nombre is not None:
        qs = qs.filter(nombre_usuario=nombre)
    if correo is not None:
        qs = qs.filter(correo__iexact=correo)
    return qs.first()


def usuario_existe(*, nombre: Optional[str] = None,
                   correo: Optional[str] = None,
                   exclude_id: Optional[int] = None) -> bool:
    cond = Q()
    if nombre is not None:
        cond |= Q(nombre_usuario=nombre)
    if correo is not None:
        cond |= Q(correo__iexact=correo)

    if not cond:
        return False

    qs = Usuario.objects.filter(cond)
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


def contar_clientes() -> int:
    return Cliente.objects.count()


# Escritura

def crear_usuario(*, nombre: str, correo: str, contrasena: str) -> Usuario:
    return Usuario.objects.create(
        nombre_usuario=nombre,
        correo=correo,
        contrasena=contrasena,
    )


def get_create_cliente(*, usuario: Usuario) -> Cliente:
    cliente, _created = Cliente.objects.get_or_create(usuario=usuario)
    return cliente


def actualizar_usuario(*, usuario_id: int, nombre: Optional[str] = None, contrasena: Optional[str] = None,
                       correo: Optional[str] = None) -> Usuario:
    fields = {}
    if nombre is not None:
        fields["nombre_usuario"] = nombre
    if contrasena is not None:
        fields["contrasena"] = contrasena
    if correo is not None:
        fields["correo"] = correo
    if fields:
        Usuario.objects.filter(pk=usuario_id).update(**fields)
    usuario = Usuario.objects.get(pk=usuario_id)
    return usuario
