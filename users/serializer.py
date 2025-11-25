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
            raise serializers.ValidationError({"Error de logica": [str(e)]})

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
            raise serializers.ValidationError({"Error de datos": [str(e)]})

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
            raise serializers.ValidationError({"Error de datos": ["Sesión inválida o expirada."]})

        try:
            usuario = serv.actualizar_datos_administrador(
                usuario_id=usuario_id,
                nombre=self.validated_data["nombre"],
                contrasena=self.validated_data["contrasena"],
                correo=self.validated_data["correo"],
            )
            return usuario
        except serv.DomainError as e:
            raise serializers.ValidationError({"Error de datos": [str(e)]})


    def save(self, **kwargs):
        if not self.is_valid():
            raise AssertionError("Debes llamar .is_valid() antes de .save()")
        return self.create(self.validated_data)


# API MOVIL SERIALIZER

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
        usuario = instance["usuario"]
        tipo = instance["tipo"]

        if tipo == "cliente":
            cliente = instance["cliente"]
            saldo = str(cliente.saldo)
            excliente = cliente.excliente
        else:
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

class AdminProfileSerializer(serializers.Serializer):
    id_usuario = serializers.IntegerField()
    nombre = serializers.CharField(max_length=10)
    correo = serializers.EmailField(max_length=50)
    contrasena = serializers.CharField(
        allow_blank=True,
        required=False,
        min_length=4
    )

    def validate(self, attrs):
        id_usuario = attrs["id_usuario"]
        nombre = attrs["nombre"]
        correo = attrs["correo"]

        # Verificar que el usuario exista
        usuario = repo.get_usuario(id=id_usuario)
        if not usuario:
            raise serializers.ValidationError("Usuario no encontrado.")

        # Validar unicidad
        if repo.usuario_existe(nombre=nombre, exclude_id=id_usuario):
            raise serializers.ValidationError("El nombre de usuario ya existe.")
        if repo.usuario_existe(correo=correo, exclude_id=id_usuario):
            raise serializers.ValidationError("El correo ya está registrado.")

        attrs["usuario"] = usuario
        return attrs

    def update(self, instance, validated_data):
        # instance es el Usuario, pero no lo usamos, usamos repo.actualizar_usuario
        usuario_id = validated_data["id_usuario"]
        nombre = validated_data["nombre"]
        correo = validated_data["correo"]
        contrasena = validated_data.get("contrasena") or None

        usuario = repo.actualizar_usuario(
            usuario_id=usuario_id,
            nombre=nombre,
            correo=correo,
            contrasena=contrasena,
        )
        return usuario

    def to_representation(self, usuario: Usuario):
        return {
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre_usuario,
            "correo": usuario.correo,
            # Igual que en la web, devolvemos la contraseña en claro
            # porque la guardas así (sin hash) y la plantilla la usa.
            "contrasena": usuario.contrasena,
        }
