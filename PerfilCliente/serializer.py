from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any

from rest_framework import serializers
from . import services as serv


class PerfilClienteSerializer(serializers.Serializer):
    nombre_usuario = serializers.CharField(min_length=1, max_length=10)
    correo = serializers.EmailField(max_length=50)
    contrasena = serializers.CharField(max_length=128, required=False, allow_blank=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        usuario_id = int(self.context["usuario_id"])
        nombre = attrs["nombre_usuario"]
        correo = attrs["correo"]
        try:
            serv.validar_usuario(usuario_id, nombre, correo)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return attrs