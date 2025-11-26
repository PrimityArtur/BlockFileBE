from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from .serializer import ValidarCategoriaSerializer
from core.utils import PER_PAGE


class AdminCategoriasListMovilView(APIView):
    """
    GET /apimovil/admin/categorias/?page=1&id=&nombre=&descripcion=
    Listado paginado de categorías para el panel de administración móvil.
    """
    # Igual que otros endpoints móviles, lo dejamos abierto por ahora
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

        filas, total_pages = ser.listar(per_page=PER_PAGE)
        page = int(ser.validated_data.get("page") or 1)

        # Misma estructura que el listar de productos (rows + page + total_pages)
        # y coherente con GestionCategorias.html
        return Response(
            {
                "ok": True,
                "rows": filas,          # [{'id', 'nombre', 'descripcion'}, ...]
                "page": page,
                "total_pages": total_pages,
            }
        )
