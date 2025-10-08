from decimal import Decimal, InvalidOperation
from typing import Optional

from rest_framework import serializers
from . import services as serv


class catalogoProductosSerializer(serializers.Serializer):
    nombre = serializers.CharField(required=False, allow_blank=True, max_length=50)
    autor = serializers.CharField(required=False, allow_blank=True, max_length=50)
    categoria = serializers.CharField(required=False, allow_blank=True, max_length=50)
    page = serializers.IntegerField(required=False, min_value=1, default=1)

    # Para “listar” con filtros desde el serializer
    def listar(self, *, per_page: int):
        d = self.validated_data
        filas, total_pages = serv.listar_pagina(
            page=int(d.get("page") or 1),
            per_page=per_page,
            f_nombre=d.get("nombre"),
            f_autor=d.get("autor"),
            f_categoria=d.get("categoria"),
        )
        return filas, total_pages

class CalificarProductoSerializer(serializers.Serializer):
    calificacion = serializers.IntegerField(min_value=1, max_value=5)


class ComentarProductoSerializer(serializers.Serializer):
    descripcion = serializers.CharField(max_length=500)
