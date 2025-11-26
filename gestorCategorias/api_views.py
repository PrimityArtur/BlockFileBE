from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from .serializer import ValidarCategoriaSerializer

PER_PAGE_MOVIL = 10


class AdminCategoriasListMovilView(APIView):
    """
    GET /apimovil/admin/categorias/listar/
    Parámetros opcionales:
      - id
      - nombre
      - descripcion
      - page
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        data = {
            "id": request.GET.get("id"),
            "nombre": request.GET.get("nombre", ""),
            "descripcion": request.GET.get("descripcion", ""),
            "page": request.GET.get("page") or 1,
        }
        ser = ValidarCategoriaSerializer(data=data)
        ser.is_valid(raise_exception=True)

        filas, total_pages = ser.listar(per_page=PER_PAGE_MOVIL)
        page = int(ser.validated_data.get("page") or 1)

        return Response({
            "ok": True,
            "page": page,
            "total_pages": total_pages,
            "rows": filas,   # cada fila: {id, nombre, descripcion}
        })
