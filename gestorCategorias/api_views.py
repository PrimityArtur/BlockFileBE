from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .serializer import ValidarCategoriaSerializer, GuardarCategoriaSerializer, EliminarCategoriaSerializer
from core.utils import PER_PAGE


class AdminCategoriasListMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        data = {
            "id": request.query_params.get("id"),
            "nombre": request.query_params.get("nombre", ""),
            "descripcion": request.query_params.get("descripcion", ""),
            "page": request.query_params.get("page", 1),
        }

        ser = ValidarCategoriaSerializer(data=data)
        ser.is_valid(raise_exception=True)

        from core.utils import PER_PAGE
        filas, total_pages = ser.listar(per_page=PER_PAGE)
        page = int(ser.validated_data.get("page") or 1)

        return Response(
            {
                "ok": True,
                "rows": filas,
                "page": page,
                "total_pages": total_pages,
            }
        )


class AdminCategoriaGuardarMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = GuardarCategoriaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        result = ser.save()  # {"id": pid}
        return Response(
            {
                "ok": True,
                "id": result["id"],
                "message": "Categoría guardada correctamente.",
            },
            status=status.HTTP_200_OK,
        )


class AdminCategoriaEliminarMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = EliminarCategoriaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.aplicar()
        return Response(
            {
                "ok": True,
                "message": "Categoría eliminada correctamente.",
            },
            status=status.HTTP_200_OK,
        )