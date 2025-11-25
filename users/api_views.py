# users/api_views.py
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from rest_framework import serializers, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Usuario, Cliente, Administrador
from . import services as serv


class LoginMovilSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=10)
    contrasena = serializers.CharField(write_only=True)

    def validate(self, attrs):
        nombre = attrs.get("nombre")
        contrasena = attrs.get("contrasena")

        if not nombre or not contrasena:
            raise serializers.ValidationError("Nombre y contraseña son obligatorios.")

        # Usamos la misma lógica que la web
        try:
            resultado = serv.autenticar_usuario(nombre=nombre, contrasena=contrasena)
        except serv.DomainError as e:
            raise serializers.ValidationError(str(e))

        usuario = resultado["usuario"]
        tipo = resultado["tipo"]  # "cliente", "administrador" o "desconocido"

        if tipo == "cliente":
            try:
                cliente = usuario.cliente
            except Cliente.DoesNotExist:
                raise serializers.ValidationError("El usuario no tiene perfil de cliente.")

            if cliente.excliente:
                raise serializers.ValidationError("Este cliente está marcado como excliente.")

            attrs["usuario"] = usuario
            attrs["tipo"] = "cliente"
            attrs["cliente"] = cliente

        elif tipo == "administrador":
            try:
                admin = usuario.administrador
            except Administrador.DoesNotExist:
                raise serializers.ValidationError("El usuario no tiene perfil de administrador.")

            if not admin.acceso:
                raise serializers.ValidationError("El acceso del administrador está deshabilitado.")

            attrs["usuario"] = usuario
            attrs["tipo"] = "administrador"
            attrs["admin"] = admin

        else:
            raise serializers.ValidationError("El usuario no tiene un rol válido.")

        return attrs

    def to_representation(self, instance):
        """
        Unificamos la respuesta para móvil:

        Siempre devolvemos:
        - id_usuario
        - nombre_usuario
        - correo
        - saldo        (para admin lo ponemos '0')
        - excliente    (para admin False)
        - tipo         ("cliente" o "administrador")
        """
        usuario = instance["usuario"]
        tipo = instance["tipo"]

        if tipo == "cliente":
            cliente = instance["cliente"]
            saldo = str(cliente.saldo)
            excliente = cliente.excliente
        else:
            # Para administrador no hay saldo de cliente
            saldo = "0"
            excliente = False

        return {
            "id_usuario": usuario.id_usuario,
            "nombre_usuario": usuario.nombre_usuario,
            "correo": usuario.correo,
            "saldo": saldo,
            "excliente": excliente,
            "tipo": tipo,
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
            "tipo": "cliente",
        }


# =========
#  Views
# =========

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
