from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from rest_framework import serializers

from core.models import Cliente, Administrador, Usuario
from . import services as serv
from . import repository as repo

class IniciarSesionSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=10)
    contrasena = serializers.CharField(write_only=True)

    def validate(self, attrs):
        nombre = attrs.get("nombre")
        contrasena = attrs.get("contrasena")

        try:
            resultado = serv.autenticar_usuario(nombre=nombre, contrasena=contrasena)
        except serv.DomainError as e:
            raise serializers.ValidationError({"Error": [str(e)]})

        # Inyectamos en validated_data lo que la view necesita
        attrs["usuario"] = resultado["usuario"]
        attrs["tipo"] = resultado["tipo"]  # 'cliente' | 'administrador' | 'desconocido'
        return attrs


class RegistrarseSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=10)
    correo = serializers.EmailField(max_length=50)
    contrasena = serializers.CharField(write_only=True, min_length=4)


    def create(self, validated_data):
        try:
            # crea Usuario y Cliente
            usuario = serv.registrar_usuario_y_cliente(
                nombre=validated_data["nombre"],
                correo=validated_data["correo"],
                contrasena=validated_data["contrasena"],
            )
            return usuario
        except serv.DomainError as e:
            raise serializers.ValidationError({"Error": [str(e)]})

    def save(self, **kwargs):
        if not self.is_valid():
            raise AssertionError("Debes llamar .is_valid() antes de .save()")
        return self.create(self.validated_data)


class AdminPerfilUpdateSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=10)
    correo = serializers.EmailField(max_length=50)
    contrasena = serializers.CharField(write_only=True, min_length=4)

    def create(self, validated_data):
        request = self.context.get("request")
        if not request:
            raise AssertionError("Falta 'request' en serializer.context.")

        usuario_id = request.session.get("usuario_id")
        if not usuario_id:
            raise serializers.ValidationError({"Error": ["Sesión inválida o expirada."]})

        try:
            usuario = serv.actualizar_datos_administrador(
                usuario_id=usuario_id,
                nombre=self.validated_data["nombre"],
                contrasena=self.validated_data["contrasena"],
                correo=self.validated_data["correo"],
            )
            return usuario
        except serv.DomainError as e:
            raise serializers.ValidationError({"Error": [str(e)]})


    def save(self, **kwargs):
        if not self.is_valid():
            raise AssertionError("Debes llamar .is_valid() antes de .save()")
        return self.create(self.validated_data)


