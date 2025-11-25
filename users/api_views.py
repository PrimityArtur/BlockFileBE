# users/api_views.py
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from rest_framework import serializers, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Usuario, Cliente, Administrador
from . import services as serv
from . import repository as repo
from .serializer import LoginMovilSerializer, RegisterMovilSerializer, AdminPerfilMovilSerializer


class LoginMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginMovilSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.validated_data["usuario"]
            tipo = serializer.validated_data["tipo"]

            # Guardamos en sesión igual que en la web, pero respetando el tipo
            request.session["usuario_id"] = usuario.id_usuario
            request.session["usuario_tipo"] = tipo  # "cliente" o "administrador"
            request.session["usuario_nombre"] = usuario.nombre_usuario
            request.session["usuario_correo"] = usuario.correo
            request.session["usuario_contrasena"] = usuario.contrasena

            data = serializer.to_representation(serializer.validated_data)
            return Response(data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterMovilSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.create(serializer.validated_data)
            data = serializer.to_representation(usuario)
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminPerfilMovilView(APIView):
    """
    API para leer/actualizar el perfil del administrador desde el móvil.

    GET  /apimovil/admin/perfil/?id_usuario=...
    PUT  /apimovil/admin/perfil/    { id_usuario, nombre, correo, contrasena }
    """
    permission_classes = [permissions.AllowAny]  # si luego quieres puedes endurecer esto

    def get(self, request, *args, **kwargs):
        usuario_id = request.query_params.get("id_usuario") or request.data.get("id_usuario")
        if not usuario_id:
            return Response({"detail": "Falta id_usuario."}, status=status.HTTP_400_BAD_REQUEST)

        usuario = repo.get_usuario(id=int(usuario_id))
        if not usuario:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminPerfilMovilSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        usuario_id = request.data.get("id_usuario")
        if not usuario_id:
            return Response({"detail": "Falta id_usuario."}, status=status.HTTP_400_BAD_REQUEST)

        usuario = repo.get_usuario(id=int(usuario_id))
        if not usuario:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminPerfilMovilSerializer(instance=usuario, data=request.data)
        if serializer.is_valid():
            actualizado = serializer.save()
            return Response(
                AdminPerfilMovilSerializer(actualizado).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)