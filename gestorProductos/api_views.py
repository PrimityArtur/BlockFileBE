from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .serializer import ValidarProductoSerializer, DetalleProductoEntradaSerializer, GuardarProductoSerializer
from . import services as serv
from .serializer import (
    ImagenEntradaSerializer,
    ReordenarImagenSerializer,
    BorrarImagenSerializer,
)
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



class AdminProductoDetalleMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk: int, *args, **kwargs):
        ser = DetalleProductoEntradaSerializer(data={"id_producto": pk})
        ser.is_valid(raise_exception=True)
        data = ser.obtener()
        if not data:
            raise Http404("Producto no encontrado")
        return Response(data)


class AdminProductoGuardarMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = GuardarProductoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = ser.save()   # {"id": pid}
        return Response({"ok": True, "id": result["id"]})



class AdminProductoArchivoMovilView(APIView):
    """
    POST /apimovil/admin/productos/archivo/
    Campos (multipart/form-data):
      - id_producto
      - archivo (file)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        pid = request.data.get("id_producto")
        archivo = request.FILES.get("archivo")

        if not pid or not archivo:
            return Response(
                {"detail": "id_producto y archivo son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pid_int = int(pid)
        except ValueError:
            return Response(
                {"detail": "id_producto inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contenido = archivo.read()
        serv.actualizar_archivo_producto(id_producto=pid_int, contenido=contenido)
        return Response({"ok": True})


class AdminProductoImagenAgregarMovilView(APIView):
    """
    POST /apimovil/admin/productos/imagenes/agregar/
    Campos (multipart/form-data):
      - id_producto
      - orden (opcional)
      - archivo (file)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        data = {
            "id_producto": request.data.get("id_producto"),
            "orden": request.data.get("orden"),
        }
        ser = ImagenEntradaSerializer(data=data)
        ser.is_valid(raise_exception=True)

        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response(
                {"detail": "archivo es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        img_id = ser.agregar(contenido=archivo.read())
        return Response({"ok": True, "id_imagen": img_id})


class AdminProductoImagenReordenarMovilView(APIView):
    """
    POST /apimovil/admin/productos/imagenes/reordenar/
    Body JSON:
      - id_imagen
      - orden
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = ReordenarImagenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.aplicar()
        return Response({"ok": True})


class AdminProductoImagenBorrarMovilView(APIView):
    """
    POST /apimovil/admin/productos/imagenes/borrar/
    Body JSON:
      - id_imagen
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = BorrarImagenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.aplicar()
        return Response({"ok": True})