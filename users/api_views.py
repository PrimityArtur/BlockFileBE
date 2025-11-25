# users/api_views.py
from decimal import Decimal
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from rest_framework import serializers, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Usuario, Cliente, Administrador
from . import services as serv
from . import repository as repo

class LoginMovilSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=10)
    contrasena = serializers.CharField(write_only=True)

    def validate(self, attrs):
        nombre = attrs.get("nombre")
        contrasena = attrs.get("contrasena")

        try:
            usuario = Usuario.objects.get(nombre_usuario=nombre)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({"detail": ["Usuario o contraseña inválidos."]})

        if usuario.contrasena != contrasena:
            raise serializers.ValidationError({"detail": ["Usuario o contraseña inválidos."]})

        # ¿Es admin?
        es_admin = Administrador.objects.filter(pk=usuario.id_usuario, acceso=True).exists()

        # ¿Es cliente?
        cliente = Cliente.objects.filter(pk=usuario.id_usuario).first()
        if cliente:
            saldo = cliente.saldo
            excliente = cliente.excliente
        else:
            saldo = Decimal("0")
            excliente = True

        attrs["id_usuario"] = usuario.id_usuario
        attrs["nombre_usuario"] = usuario.nombre_usuario
        attrs["correo"] = usuario.correo
        attrs["saldo"] = str(saldo)
        attrs["excliente"] = excliente
        attrs["es_admin"] = es_admin

        return attrs

    def to_representation(self, instance):
        """
        instance es self.validated_data
        """
        return {
            "id_usuario": instance["id_usuario"],
            "nombre_usuario": instance["nombre_usuario"],
            "correo": instance["correo"],
            "saldo": instance["saldo"],
            "excliente": instance["excliente"],
            "es_admin": instance["es_admin"],
        }


class LoginMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginMovilSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.to_representation(serializer.validated_data)
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterMovilSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=10)
    correo = serializers.EmailField(max_length=50)
    contrasena = serializers.CharField(write_only=True, min_length=4, max_length=128)

    def validate_correo(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Correo inválido.")
        if Usuario.objects.filter(correo__iexact=value).exists():
            raise serializers.ValidationError("El correo ya está registrado.")
        return value

    def validate_nombre(self, value):
        if Usuario.objects.filter(nombre_usuario=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya existe.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        usuario = Usuario.objects.create(
            nombre_usuario=validated_data["nombre"],
            correo=validated_data["correo"],
            contrasena=validated_data["contrasena"],
        )
        # Crear cliente por defecto
        Cliente.objects.create(
            usuario=usuario,
            excliente=False,
            saldo=Decimal("0.00"),
        )
        return usuario

    def to_representation(self, usuario: Usuario):
        cliente = Cliente.objects.filter(pk=usuario.id_usuario).first()
        saldo = cliente.saldo if cliente else Decimal("0")
        excliente = cliente.excliente if cliente else True
        return {
            "id_usuario": usuario.id_usuario,
            "nombre_usuario": usuario.nombre_usuario,
            "correo": usuario.correo,
            "saldo": str(saldo),
            "excliente": excliente,
        }


class RegisterMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterMovilSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.create(serializer.validated_data)
            data = serializer.to_representation(usuario)
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class AdminProfileSerializer(serializers.Serializer):
    id_usuario = serializers.IntegerField()
    nombre = serializers.CharField(max_length=10)
    correo = serializers.EmailField(max_length=50)
    contrasena = serializers.CharField(max_length=128, min_length=4)

    def validate(self, attrs):
        # Aquí podrías llamar a un servicio para validar unicidad, etc.
        return attrs

    def to_representation(self, usuario: Usuario):
        return {
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre_usuario,
            "correo": usuario.correo,
            "contrasena": usuario.contrasena,
        }


class AdminProfileMovilView(APIView):
    """
    GET  /apimovil/admin/perfil/?id_usuario=XX  -> datos del admin
    POST /apimovil/admin/perfil/                -> actualizar datos del admin
    """
    permission_classes = [permissions.AllowAny]  # si luego manejas auth, cámbialo

    def get(self, request, *args, **kwargs):
        id_usuario = request.query_params.get("id_usuario")
        if not id_usuario:
            return Response({"detail": "id_usuario es requerido."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            id_usuario = int(id_usuario)
        except ValueError:
            return Response({"detail": "id_usuario inválido."},
                            status=status.HTTP_400_BAD_REQUEST)

        usuario = repo.get_usuario(id=id_usuario)
        if not usuario:
            return Response({"detail": "Usuario no encontrado."},
                            status=status.HTTP_404_NOT_FOUND)

        # Verificar que sea administrador
        if not Administrador.objects.filter(pk=id_usuario, acceso=True).exists():
            return Response({"detail": "No tienes permisos de administrador."},
                            status=status.HTTP_403_FORBIDDEN)

        ser = AdminProfileSerializer()
        data = ser.to_representation(usuario)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        ser = AdminProfileSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data
        usuario_id = data["id_usuario"]
        try:
            usuario_actualizado = serv.actualizar_datos_administrador(
                usuario_id=usuario_id,
                nombre=data["nombre"],
                correo=data["correo"],
                contrasena=data["contrasena"],
            )
        except serv.DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        out_ser = AdminProfileSerializer()
        out_data = out_ser.to_representation(usuario_actualizado)
        return Response(out_data, status=status.HTTP_200_OK)