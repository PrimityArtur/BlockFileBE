from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from .serializer import ValidarProductoSerializer
from core.utils import PER_PAGE


class AdminProductosListMovilView(APIView):
    """
    GET /apimovil/admin/productos/?page=1&id=&nombre=&autor=&categoria=
    Devuelve el listado paginado de productos para el panel de administración móvil.
    """
    # Igual que AdminProfileMovilView, por ahora sin restricción
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        data = {
            "id": request.query_params.get("id"),
            "nombre": request.query_params.get("nombre", ""),
            "autor": request.query_params.get("autor", ""),
            "categoria": request.query_params.get("categoria", ""),
            "page": request.query_params.get("page", 1),
        }

        ser = ValidarProductoSerializer(data=data)
        ser.is_valid(raise_exception=True)

        filas, total_pages = ser.listar(per_page=PER_PAGE)
        page = int(ser.validated_data.get("page", 1))

        # Misma estructura que el api_listar de Gestión de Productos
        return Response(
            {
                "ok": True,
                "rows": filas,          # [{'id', 'nombre', 'autor', 'categoria', 'promedio'}, ...]
                "page": page,
                "total_pages": total_pages,
            }
        )
