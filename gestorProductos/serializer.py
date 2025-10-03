from decimal import Decimal, InvalidOperation
from typing import Optional

from rest_framework import serializers
from . import services as serv


class ValidarProductoSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
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
            f_id=d.get("id"),
            f_nombre=d.get("nombre"),
            f_autor=d.get("autor"),
            f_categoria=d.get("categoria"),
        )
        return filas, total_pages


class GuardarProductoSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    nombre = serializers.CharField(max_length=50)
    descripcion = serializers.CharField(allow_blank=True, required=False)
    version = serializers.CharField(allow_blank=True, required=False, max_length=50)
    precio = serializers.CharField()
    id_autor = serializers.IntegerField(required=False, allow_null=True)
    id_categoria = serializers.IntegerField(required=False, allow_null=True)
    activo = serializers.BooleanField(default=True)

    def validate_precio(self, v):
        try:
            d = Decimal(v)
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError('precio inválido')
        if d < 0:
            raise serializers.ValidationError('precio debe ser >= 0')
        return str(d)

    # DRF: view -> serializer.is_valid() -> serializer.save() -> create/update
    def create(self, validated_data):
        pid = serv.guardar_producto(**validated_data)
        return {"id": pid}

    # Si quisieras soportar update via instance, aquí delegas igual:
    def update(self, instance, validated_data):
        pid = serv.guardar_producto(**validated_data)
        return {"id": pid}


class ImagenEntradaSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField()
    orden = serializers.IntegerField(required=False)

    def agregar(self, *, contenido: bytes) -> int:
        d = self.validated_data
        return serv.agregar_imagen(id_producto=d["id_producto"], contenido=contenido, orden=d.get("orden"))


class ReordenarImagenSerializer(serializers.Serializer):
    id_imagen = serializers.IntegerField()
    orden = serializers.IntegerField()

    def aplicar(self):
        serv.reordenar_imagen(id_imagen=self.validated_data["id_imagen"], nuevo_orden=self.validated_data["orden"])


class BorrarImagenSerializer(serializers.Serializer):
    id_imagen = serializers.IntegerField()

    def aplicar(self):
        serv.borrar_imagen(id_imagen=self.validated_data["id_imagen"])


class EliminarProductoSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField()

    def aplicar(self):
        serv.eliminar_producto(id_producto=self.validated_data["id_producto"])


class DetalleProductoEntradaSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField()

    def obtener(self):
        return serv.obtener_detalle(self.validated_data["id_producto"])
