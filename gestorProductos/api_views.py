from django.db import connection
from django.http import Http404, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser

from .serializer import ValidarProductoSerializer, DetalleProductoEntradaSerializer, GuardarProductoSerializer
from . import services as serv
from .serializer import (
    ImagenEntradaSerializer,
    ReordenarImagenSerializer,
    BorrarImagenSerializer,
)
from core.utils import PER_PAGE


class AdminProductosListMovilView(APIView):
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
                "rows": filas,
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

        # Añadir URL absoluta para cada imagen
        imagenes = data.get("imagenes", [])
        base_url = request.build_absolute_uri("/")
        base_url = base_url.replace("http://", "https://")[:-1]
        for img in imagenes:
            img_id = img["id"]
            img["url"] = f"{base_url}/apimovil/admin/productos/imagenes/archivo/{img_id}/"

        return Response(data)


class AdminProductoGuardarMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = GuardarProductoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = ser.save()   # {"id": pid}
        return Response({"ok": True, "id": result["id"]})



class AdminProductoArchivoMovilView(APIView):
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
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # ---- id_producto ----
        raw_id = request.data.get("id_producto")
        if not raw_id:
            return Response(
                {"detail": "id_producto es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            id_producto = int(raw_id)
        except ValueError:
            return Response(
                {"detail": "id_producto inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- orden (opcional) ----
        raw_orden = request.data.get("orden")
        orden = None
        if raw_orden not in (None, "", "null"):
            try:
                orden = int(raw_orden)
            except ValueError:
                return Response(
                    {"detail": "orden inválido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ---- archivo ----
        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response(
                {"detail": "archivo es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guardar imagen en BD
        img_id = serv.agregar_imagen(
            id_producto=id_producto,
            contenido=archivo.read(),
            orden=orden,
        )

        return Response({"ok": True, "id_imagen": img_id})


class AdminProductoImagenReordenarMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = ReordenarImagenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.aplicar()
        return Response({"ok": True})


class AdminProductoImagenBorrarMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        ser = BorrarImagenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.aplicar()
        return Response({"ok": True})





class AdminProductoImagenArchivoMovilView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk: int, *args, **kwargs):
        sql = '''
            SELECT archivo
            FROM "IMAGEN_PRODUCTO"
            WHERE id_imagen_producto = %s
            LIMIT 1;
        '''
        with connection.cursor() as cur:
            cur.execute(sql, [pk])
            row = cur.fetchone()

        if not row or not row[0]:
            raise Http404("Imagen no encontrada")

        blob = bytes(row[0])
        # Si en tu BD no guardas el mime, usa un genérico; Coil lo maneja bien
        return HttpResponse(blob, content_type="image/*")