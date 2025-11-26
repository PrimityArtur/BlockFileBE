# gestorCategorias/api_views.py
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from core.utils import PER_PAGE
from .serializer import (
    ValidarCategoriaSerializer,
    GuardarCategoriaSerializer,
    EliminarCategoriaSerializer,
    DetalleCategoriaEntradaSerializer,
)


class AdminCategoriasListMovilView(APIView):
    """
    GET /apimovil/admin/categorias/listar/
    Query params: id, nombre, descripcion, page
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        data = {
            "id": request.query_params.get("id"),
            "nombre": request.query_params.get("nombre"),
            "descripcion": request.query_params.get("descripcion"),
            "page": request.query_params.get("page") or 1,
        }
        ser = ValidarCategoriaSerializer(data=data)
        ser.is_valid(raise_exception=True)
        filas, total_pages = ser.listar(per_page=PER_PAGE)
        return Response(
            {
                "ok": True,
                "rows": filas,
                "page": int(ser.validated_data.get("page") or 1),
                "total_pages": total_pages,
            }
        )


class AdminCategoriaDetalleMovilView(APIView):
    """
    GET /apimovil/admin/categorias/detalle/<id>/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk: int, *args, **kwargs):
        ser = DetalleCategoriaEntradaSerializer(data={"id_categoria": pk})
        ser.is_valid(raise_exception=True)
        data = ser.obtener()
        if not data:
            raise Http404("Categoría no encontrada")
        return Response(data)


class AdminCategoriaGuardarMovilView(APIView):
    """
    POST /apimovil/admin/categorias/guardar/
    Body JSON:
      { "id": null|int, "nombre": "...", "descripcion": "..." }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = GuardarCategoriaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = ser.save()  # {"id": pid}
        return Response(
            {"ok": True, "id": result["id"]},
            status=status.HTTP_200_OK,
        )


class AdminCategoriaEliminarMovilView(APIView):
    """
    POST /apimovil/admin/categorias/eliminar/<id>/
    (Para usar más adelante en el app)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk: int, *args, **kwargs):
        ser = EliminarCategoriaSerializer(data={"id_categoria": pk})
        ser.is_valid(raise_exception=True)
        ser.aplicar()
        return Response({"ok": True})
