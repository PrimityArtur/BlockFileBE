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
        nombre = (attrs.get("nombre") or "").strip()
        contrasena = attrs.get("contrasena") or ""

        if not nombre or not contrasena:
            raise serializers.ValidationError("Nombre y contraseña son obligatorios.")

        # Usamos la lógica de dominio compartida
        try:
            result = serv.autenticar_usuario(nombre=nombre, contrasena=contrasena)
        except serv.DomainError as e:
            raise serializers.ValidationError(str(e))

        usuario = result["usuario"]
        tipo = result.get("tipo") or "desconocido"

        data = {"usuario": usuario, "tipo": tipo}

        if tipo == "cliente":
            # Aseguramos que tenga perfil de cliente y que no sea excliente
            try:
                cliente = Cliente.objects.get(pk=usuario.id_usuario)
            except Cliente.DoesNotExist:
                raise serializers.ValidationError("El usuario no tiene perfil de cliente.")

            if cliente.excliente:
                raise serializers.ValidationError("Este cliente está marcado como excliente.")

            data["cliente"] = cliente

        elif tipo == "administrador":
            # Verificamos que realmente exista el registro de Administrador
            if not Administrador.objects.filter(pk=usuario.id_usuario).exists():
                raise serializers.ValidationError("No tienes permisos de administrador.")

        attrs.update(data)
        return attrs

    def to_representation(self, instance):
        """
        instance es el diccionario que armamos en validate():
        { "usuario": Usuario, "tipo": str, "cliente": Cliente? }
        """
        usuario = instance["usuario"]
        tipo = instance.get("tipo") or "desconocido"

        saldo = "0.00"
        excliente = False

        if tipo == "cliente":
            cliente = instance["cliente"]
            saldo = str(cliente.saldo)
            excliente = cliente.excliente

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

    def validate_correo(self, value: str) -> str:
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Correo inválido.")
        return value

    def validate(self, attrs):
        nombre = (attrs.get("nombre") or "").strip()
        correo = (attrs.get("correo") or "").strip()
        contrasena = attrs.get("contrasena") or ""
        if not nombre or not correo or not contrasena:
            raise serializers.ValidationError("Nombre, correo y contraseña son obligatorios.")
        attrs["nombre"] = nombre
        attrs["correo"] = correo
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        try:
            usuario = serv.registrar_usuario_y_cliente(
                nombre=validated_data["nombre"],
                correo=validated_data["correo"],
                contrasena=validated_data["contrasena"],
            )
        except serv.DomainError as e:
            raise serializers.ValidationError(str(e))
        return usuario

    def to_representation(self, instance: Usuario):
        # Obtenemos el cliente asociado para devolver saldo y excliente
        try:
            cliente = Cliente.objects.get(pk=instance.id_usuario)
            saldo = str(cliente.saldo)
            excliente = cliente.excliente
        except Cliente.DoesNotExist:
            saldo = "0.00"
            excliente = False

        return {
            "id_usuario": instance.id_usuario,
            "nombre_usuario": instance.nombre_usuario,
            "correo": instance.correo,
            "saldo": saldo,
            "excliente": excliente,
        }


class LoginMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginMovilSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.validated_data["usuario"]
            tipo = serializer.validated_data.get("tipo") or "desconocido"

            # Guardar en sesión (igual que en la web, pero respetando el tipo)
            request.session["usuario_id"] = usuario.id_usuario
            request.session["usuario_tipo"] = tipo
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
            usuario = serializer.save()
            data = serializer.to_representation(usuario)
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminPerfilMovilView(APIView):
    """
    GET  /apimovil/admin/perfil/?id_usuario=...
        -> devuelve AdminProfileDto
    POST /apimovil/admin/perfil/
        body: AdminProfileDto
        -> actualiza y devuelve AdminProfileDto
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            id_usuario = int(request.query_params.get("id_usuario") or 0)
        except (TypeError, ValueError):
            return Response({"detail": "id_usuario inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if id_usuario <= 0:
            return Response({"detail": "id_usuario es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = Usuario.objects.get(pk=id_usuario)
        except Usuario.DoesNotExist:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if not Administrador.objects.filter(pk=id_usuario).exists():
            return Response({"detail": "No tienes permisos de administrador."}, status=status.HTTP_403_FORBIDDEN)

        data = {
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre_usuario,
            "correo": usuario.correo,
            "contrasena": usuario.contrasena,
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        body = request.data or {}
        try:
            id_usuario = int(body.get("id_usuario") or 0)
        except (TypeError, ValueError):
            return Response({"detail": "id_usuario inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if id_usuario <= 0:
            return Response({"detail": "id_usuario es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        nombre = (body.get("nombre") or "").strip()
        correo = (body.get("correo") or "").strip()
        contrasena = body.get("contrasena") or ""

        if not nombre or not correo or not contrasena:
            return Response(
                {"detail": "Nombre, correo y contraseña son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validamos el correo con el mismo validador que antes
        try:
            validate_email(correo)
        except DjangoValidationError:
            return Response({"detail": "Correo inválido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = serv.actualizar_datos_administrador(
                usuario_id=id_usuario,
                nombre=nombre,
                contrasena=contrasena,
                correo=correo,
            )
        except serv.DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Si es el mismo usuario que está en sesión, actualizamos la sesión también
        if request.session.get("usuario_id") == usuario.id_usuario:
            request.session["usuario_nombre"] = usuario.nombre_usuario
            request.session["usuario_correo"] = usuario.correo
            request.session["usuario_contrasena"] = usuario.contrasena

        data = {
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre_usuario,
            "correo": usuario.correo,
            "contrasena": usuario.contrasena,
        }
        return Response(data, status=status.HTTP_200_OK)
