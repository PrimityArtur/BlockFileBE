from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json

from . import services as serv
from .serializer import PerfilClienteSerializer
from . import repository as repo

MOBILE_PER_PAGE = 6


def _get_usuario_id(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return None
    try:
        return int(usuario_id)
    except (TypeError, ValueError):
        return None


@require_http_methods(["GET"])
def api_perfil_cliente(request):
    usuario_id = _get_usuario_id(request)
    if not usuario_id:
        return JsonResponse({"ok": False, "error": "No autenticado."}, status=401)

    perfil = serv.obtener_perfil_cliente(usuario_id)
    if not perfil:
        return JsonResponse({"ok": False, "error": "Perfil no encontrado."}, status=404)

    # Por seguridad NO devolvemos la contraseña
    perfil_dict = {
        "id_usuario": perfil["id_usuario"],
        "nombre_usuario": perfil["nombre_usuario"],
        "correo": perfil["correo"],
        "saldo": str(perfil["saldo"] or "0.00"),
        "num_compras": int(perfil["num_compras"] or 0),
    }
    return JsonResponse({"ok": True, "perfil": perfil_dict}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def api_actualizar_perfil_cliente(request):
    usuario_id = _get_usuario_id(request)
    if not usuario_id:
        return JsonResponse({"ok": False, "error": "No autenticado."}, status=401)

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido.")

    ser = PerfilClienteSerializer(data=data, context={"usuario_id": usuario_id})
    if not ser.is_valid():
        return JsonResponse({"ok": False, "errors": ser.errors}, status=400)

    v = ser.validated_data
    with transaction.atomic():
        serv.actualizar_perfil_cliente(
            usuario_id=usuario_id,
            nombre_usuario=v["nombre_usuario"],
            correo=v["correo"],
            contrasena=v.get("contrasena") or None,
        )

    # devolvemos perfil actualizado
    perfil = serv.obtener_perfil_cliente(usuario_id) or {}
    perfil_dict = {
        "id_usuario": perfil["id_usuario"],
        "nombre_usuario": perfil["nombre_usuario"],
        "correo": perfil["correo"],
        "saldo": str(perfil["saldo"] or "0.00"),
        "num_compras": int(perfil["num_compras"] or 0),
    }
    return JsonResponse({"ok": True, "perfil": perfil_dict}, status=200)


@require_http_methods(["GET"])
def api_compras_cliente(request):
    usuario_id = _get_usuario_id(request)
    if not usuario_id:
        return JsonResponse({"ok": False, "error": "No autenticado."}, status=401)

    try:
        page = int(request.GET.get("page", "1") or 1)
    except ValueError:
        page = 1

    filas, total_pages = repo.compras_cliente(usuario_id, page, MOBILE_PER_PAGE)
    return JsonResponse(
        {
            "ok": True,
            "rows": filas,
            "page": page,
            "total_pages": total_pages,
        },
        status=200,
    )
