# users/api_views.py
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from rest_framework import serializers, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Usuario, Cliente, Administrador
from . import repository as repo
from . import services as serv


# ============================================================
# LOGIN MÓVIL (CLIENTE o ADMIN) con sesión + es_admin
# ============================================================

class LoginMovilSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=10)
    contrasena = serializers.CharField(write_only=True)

    def validate(self, attrs):
        nombre = attrs.get("nombre")
        contrasena = attrs.get("contrasena")

        if not nombre or not contrasena:
            raise serializers.ValidationError("Nombre y contraseña son obligatorios.")

        # Usamos el servicio común para autenticar
        try:
            data = serv.autenticar_usuario(nombre=nombre, contrasena=contrasena)
        except serv.DomainError as e:
            raise serializers.ValidationError(str(e))

        usuario = data["usuario"]
        tipo = data["tipo"]  # "cliente", "administrador" o "desconocido"

        cliente = None
        if tipo == "cliente":
            # Debe tener perfil de cliente y no ser excliente
            try:
                cliente = Cliente.objects.get(pk=usuario.id_usuario)
            except Cliente.DoesNotExist:
                raise serializers.ValidationError("El usuario no tiene perfil de cliente.")

            if cliente.excliente:
                raise serializers.ValidationError("Este cliente está marcado como excliente.")

        # Para admins intentamos obtener Cliente solo si existe, pero no es obligatorio.
        elif tipo == "administrador":
            cliente = Cliente.objects.filter(pk=usuario.id_usuario).first()

        # Si no es cliente ni administrador, no dejamos entrar
        if tipo not in ("cliente", "administrador"):
            raise serializers.ValidationError("El usuario no tiene rol válido para el acceso móvil.")

        attrs["usuario"] = usuario
        attrs["tipo"] = tipo
        attrs["cliente"] = cliente
        return attrs

    def to_representation(self, instance):
        usuario = instance["usuario"]
        tipo = instance["tipo"]
        cliente = instance["cliente"]

        saldo = "0.00"
        excliente = True
        if cliente is not None:
            saldo = str(cliente.saldo)
            excliente = cliente.excliente

        es_admin = (tipo == "administrador")

        return {
            "id_usuario": usuario.id_usuario,
            "nombre_usuario": usuario.nombre_usuario,
            "correo": usuario.correo,
            "saldo": saldo,
            "excliente": excliente,
            "es_admin": es_admin,
        }


class LoginMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginMovilSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.validated_data["usuario"]
            tipo = serializer.validated_data["tipo"]

            # === IMPORTANTE: restaurar la sesión como antes ===
            request.session["usuario_id"] = usuario.id_usuario
            request.session["usuario_tipo"] = tipo  # "cliente" o "administrador"
            request.session["usuario_nombre"] = usuario.nombre_usuario
            request.session["usuario_correo"] = usuario.correo
            request.session["usuario_contrasena"] = usuario.contrasena

            data = serializer.to_representation(serializer.validated_data)
            return Response(data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# REGISTRO MÓVIL (solo clientes)
# ============================================================

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
        contrasena = attrs.get("contrasena")

        if not nombre or not correo or not contrasena:
            raise serializers.ValidationError("Nombre, correo y contraseña son obligatorios.")

        # Verificamos duplicados usando el servicio/repositorio
        if repo.usuario_existe(nombre=nombre):
            raise serializers.ValidationError("El nombre de usuario ya existe.")
        if repo.usuario_existe(correo=correo):
            raise serializers.ValidationError("El correo ya está registrado.")

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Usamos el servicio que crea Usuario + Cliente
        usuario = serv.registrar_usuario_y_cliente(
            nombre=validated_data["nombre"],
            correo=validated_data["correo"],
            contrasena=validated_data["contrasena"],
        )
        return usuario

    def to_representation(self, usuario: Usuario):
        # conseguir cliente asociado
        cliente = Cliente.objects.filter(pk=usuario.id_usuario).first()
        saldo = cliente.saldo if cliente else 0
        excliente = cliente.excliente if cliente else False

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

            # Opcional: también iniciar sesión al registrarse
            request.session["usuario_id"] = usuario.id_usuario
            request.session["usuario_tipo"] = "cliente"
            request.session["usuario_nombre"] = usuario.nombre_usuario
            request.session["usuario_correo"] = usuario.correo
            request.session["usuario_contrasena"] = usuario.contrasena

            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# PERFIL ADMINISTRADOR PARA MÓVIL
# ============================================================

class AdminProfileSerializer(serializers.Serializer):
    id_usuario = serializers.IntegerField()
    nombre = serializers.CharField(max_length=10)
    correo = serializers.EmailField(max_length=50)
    contrasena = serializers.CharField(max_length=128, min_length=4)

    def validate(self, attrs):
        # Podrías añadir más validaciones si quieres
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
        print(data)
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
