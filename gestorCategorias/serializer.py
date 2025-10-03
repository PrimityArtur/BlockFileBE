from decimal import Decimal, InvalidOperation
from typing import Optional

from rest_framework import serializers
from . import services as serv


class ValidarCategoriaSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    nombre = serializers.CharField(required=False, allow_blank=True, max_length=50)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)

    # Para “listar” con filtros desde el serializer
    def listar(self, *, per_page: int):
        d = self.validated_data
        filas, total_pages = serv.listar_pagina(
            page=int(d.get("page") or 1),
            per_page=per_page,
            f_id=d.get("id"),
            f_nombre=d.get("nombre"),
            f_descripcion=d.get("descripcion"),
        )
        return filas, total_pages


class GuardarCategoriaSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    nombre = serializers.CharField(max_length=50)
    descripcion = serializers.CharField(allow_blank=True, required=False)

    # DRF: view -> serializer.is_valid() -> serializer.save() -> create/update
    def create(self, validated_data):
        pid = serv.guardar_categoria(**validated_data)
        return {"id": pid}

    # Si quisieras soportar update via instance, aquí delegas igual:
    def update(self, instance, validated_data):
        pid = serv.guardar_categoria(**validated_data)
        return {"id": pid}


class EliminarCategoriaSerializer(serializers.Serializer):
    id_categoria = serializers.IntegerField()

    def aplicar(self):
        serv.eliminar_categoria(id_categoria=self.validated_data["id_categoria"])


class DetalleCategoriaEntradaSerializer(serializers.Serializer):
    id_categoria = serializers.IntegerField()

    def obtener(self):
        return serv.obtener_detalle(self.validated_data["id_categoria"])
