from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializer import (
    ValidarCategoriaSerializer,
    GuardarCategoriaSerializer,
    EliminarCategoriaSerializer,
    DetalleCategoriaEntradaSerializer,
)


class AdminCategoriasListApi(APIView):
    """
    GET /apimovil/admin/categorias/listar/
    ?page=1&id=...&nombre=...&descripcion=...
    """
    def get(self, request, *args, **kwargs):
        s = ValidarCategoriaSerializer(data=request.query_params)
        if not s.is_valid():
            return Response(
                {"ok": False, "errors": s.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Puedes controlar el PER_PAGE específico para móvil aquí si quieres
        filas, total_pages = s.listar(per_page=10)
        page = s.validated_data.get("page") or 1

        return Response(
            {
                "ok": True,
                "rows": filas,
                "page": page,
                "total_pages": total_pages,
            },
            status=status.HTTP_200_OK,
        )


class AdminCategoriasDetalleApi(APIView):
    """
    GET /apimovil/admin/categorias/detalle/<int:id_categoria>/
    """
    def get(self, request, id_categoria: int, *args, **kwargs):
        s = DetalleCategoriaEntradaSerializer(data={"id_categoria": id_categoria})
        if not s.is_valid():
            return Response(
                {"ok": False, "errors": s.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        detalle = s.obtener()
        if not detalle:
            return Response(
                {"ok": False, "detail": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(detalle, status=status.HTTP_200_OK)


class AdminCategoriasGuardarApi(APIView):
    """
    POST /apimovil/admin/categorias/guardar/
    Body JSON: { "id": null|int, "nombre": "...", "descripcion": "..." }
    """
    def post(self, request, *args, **kwargs):
        s = GuardarCategoriaSerializer(data=request.data)
        if not s.is_valid():
            return Response(
                {"ok": False, "errors": s.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = s.save()   # -> {"id": ...}
        return Response(
            {"ok": True, **data},
            status=status.HTTP_200_OK,
        )


class AdminCategoriasEliminarApi(APIView):
    """
    POST /apimovil/admin/categorias/eliminar/<int:id_categoria>/
    """
    def post(self, request, id_categoria: int, *args, **kwargs):
        s = EliminarCategoriaSerializer(data={"id_categoria": id_categoria})
        if not s.is_valid():
            return Response(
                {"ok": False, "errors": s.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        s.aplicar()
        return Response({"ok": True}, status=status.HTTP_200_OK)
