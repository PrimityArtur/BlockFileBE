from decimal import Decimal, InvalidOperation
from typing import Optional

from rest_framework import serializers
from . import services as serv


class ValidarUsuarioSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    nombre = serializers.CharField(required=False, allow_blank=True, max_length=50)
    saldo = serializers.DecimalField(allow_null=True, required=False, max_digits=12, decimal_places=2, min_value=0)
    page = serializers.IntegerField(required=False, min_value=1, default=1)

    # Para “listar” con filtros desde el serializer
    def listar(self, *, per_page: int):
        d = self.validated_data
        filas, total_pages = serv.listar_pagina(
            page=int(d.get("page") or 1),
            per_page=per_page,
            f_id=d.get("id"),
            f_nombre=d.get("nombre"),
            f_saldo=d.get("saldo"),
        )
        return filas, total_pages


class GuardarUsuarioSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    saldo = serializers.DecimalField(allow_null=True, required=False, max_digits=12, decimal_places=2, min_value=0)

    # DRF: view -> serializer.is_valid() -> serializer.save() -> create/update
    def create(self, validated_data):
        pid = serv.guardar_usuario(**validated_data)
        return {"id": pid}

    # Si quisieras soportar update via instance, aquí delegas igual:
    def update(self, instance, validated_data):
        pid = serv.guardar_usuario(**validated_data)
        return {"id": pid}


class EliminarUsuarioSerializer(serializers.Serializer):
    id_usuario = serializers.IntegerField()

    def aplicar(self):
        serv.eliminar_usuario(id_usuario=self.validated_data["id_usuario"])


class DetalleUsuarioEntradaSerializer(serializers.Serializer):
    id_usuario = serializers.IntegerField()

    def obtener(self):
        return serv.obtener_detalle(self.validated_data["id_usuario"])
