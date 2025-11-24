# users/api.py
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from rest_framework import serializers, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Usuario, Cliente


class LoginMovilSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=10)
    contrasena = serializers.CharField(write_only=True)

    def validate(self, attrs):
        nombre = attrs.get("nombre")
        contrasena = attrs.get("contrasena")

        if not nombre or not contrasena:
            raise serializers.ValidationError("Nombre y contraseña son obligatorios.")

        try:
            usuario = Usuario.objects.get(nombre_usuario=nombre)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Usuario o contraseña inválidos.")

        if usuario.contrasena != contrasena:
            # En tu proyecto no usas hash, es comparación directa
            raise serializers.ValidationError("Usuario o contraseña inválidos.")

        # Asegurar que sea cliente activo
        try:
            cliente = usuario.cliente
        except Cliente.DoesNotExist:
            raise serializers.ValidationError("El usuario no tiene perfil de cliente.")

        if cliente.excliente:
            raise serializers.ValidationError("Este cliente está marcado como excliente.")

        attrs["usuario"] = usuario
        attrs["cliente"] = cliente
        return attrs

    def to_representation(self, instance):
        usuario = instance["usuario"]
        cliente = instance["cliente"]
        return {
            "id_usuario": usuario.id_usuario,
            "nombre_usuario": usuario.nombre_usuario,
            "correo": usuario.correo,
            "saldo": str(cliente.saldo),
            "excliente": cliente.excliente,
        }


class RegisterMovilSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=10)
    correo = serializers.CharField(max_length=50)
    contrasena = serializers.CharField(write_only=True, min_length=4)

    def validate_correo(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Correo inválido.")
        return value

    def validate(self, attrs):
        nombre = attrs.get("nombre")
        correo = attrs.get("correo")

        # Validaciones básicas
        if not nombre or not correo:
            raise serializers.ValidationError("Nombre y correo son obligatorios.")

        # Verificar unicidad individuales y combinadas (por seguridad)
        if Usuario.objects.filter(nombre_usuario=nombre).exists():
            raise serializers.ValidationError("El nombre de usuario ya existe.")
        if Usuario.objects.filter(correo=correo).exists():
            raise serializers.ValidationError("El correo ya está registrado.")

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            usuario = Usuario.objects.create(
                nombre_usuario=validated_data["nombre"],
                correo=validated_data["correo"],
                contrasena=validated_data["contrasena"],  # sin hash, igual que login
            )
            Cliente.objects.create(usuario=usuario)

        return usuario

    def to_representation(self, usuario: Usuario):
        # obtener cliente
        cliente = usuario.cliente
        return {
            "id_usuario": usuario.id_usuario,
            "nombre_usuario": usuario.nombre_usuario,
            "correo": usuario.correo,
            "saldo": str(cliente.saldo),
            "excliente": cliente.excliente,
        }


# =========
#  Views
# =========

class LoginMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginMovilSerializer(data=request.data)
        if serializer.is_valid():
            # Recuperar usuario y cliente validados
            usuario = serializer.validated_data["usuario"]
            cliente = serializer.validated_data["cliente"]

            # === GUARDAR EN SESIÓN IGUAL QUE EN LA WEB ===
            request.session["usuario_id"] = usuario.id_usuario
            request.session["usuario_tipo"] = "cliente"
            request.session["usuario_nombre"] = usuario.nombre_usuario
            request.session["usuario_correo"] = usuario.correo
            request.session["usuario_contrasena"] = usuario.contrasena

            # Representación JSON (igual que antes)
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
