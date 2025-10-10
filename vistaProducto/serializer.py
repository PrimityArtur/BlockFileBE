from decimal import Decimal, InvalidOperation
from typing import Optional

from rest_framework import serializers
from . import services as serv


class CalificarProductoSerializer(serializers.Serializer):
    calificacion = serializers.IntegerField(min_value=1, max_value=5)


class ComentarProductoSerializer(serializers.Serializer):
    descripcion = serializers.CharField(max_length=500)
