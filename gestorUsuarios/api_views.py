from decimal import Decimal
from typing import Optional

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .serializer import (
    ValidarUsuarioSerializer,
    GuardarUsuarioSerializer,
    EliminarUsuarioSerializer,
)
from . import services as serv
from core.utils import PER_PAGE


class AdminUsuariosListMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        data = {
            "id": request.query_params.get("id"),
            "nombre": request.query_params.get("nombre", ""),
            "saldo": request.query_params.get("saldo"),
            "page": request.query_params.get("page", 1),
        }

        ser = ValidarUsuarioSerializer(data=data)
        ser.is_valid(raise_exception=True)

        filas, total_pages = ser.listar(per_page=PER_PAGE)
        page = int(ser.validated_data.get("page") or 1)

        return Response(
            {
                "ok": True,
                "rows": filas,  # [{id, nombre, saldo}]
                "page": page,
                "total_pages": total_pages,
            }
        )


class AdminUsuarioDetalleMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id_usuario: int, *args, **kwargs):
        detalle = serv.obtener_detalle(id_usuario=id_usuario)
        if not detalle:
            return Response(
                {"ok": False, "detail": "Usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "ok": True,
                "id": detalle["id"],
                "nombre": detalle["nombre"],
                "correo": detalle["correo"],
                "fecha": detalle["fecha"],
                "saldo": str(detalle["saldo"]) if detalle["saldo"] is not None else None,
            }
        )


class AdminUsuarioGuardarMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = GuardarUsuarioSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = ser.save()  # {"id": pid}

        return Response(
            {
                "ok": True,
                "id": result["id"],
                "message": "Usuario guardado correctamente.",
            },
            status=status.HTTP_200_OK,
        )


class AdminUsuarioEliminarMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = EliminarUsuarioSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.aplicar()
        return Response(
            {
                "ok": True,
                "message": "Usuario eliminado correctamente.",
            },
            status=status.HTTP_200_OK,
        )
