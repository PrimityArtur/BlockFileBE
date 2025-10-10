import magic

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, Http404
from django.middleware.csrf import get_token
import json

from core.models import ImagenProducto
from . import serializer as serial
from . import repository as repo
from . import services as serv
from core.utils import PER_PAGE

@require_http_methods(["GET", "POST"])
def perfil_cliente_view(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("users:logout")
    page = int(request.GET.get("page") or 1)

    if request.method == "POST":
        ser = serial.PerfilClienteSerializer(
            data={
                "nombre_usuario": (request.POST.get("nombre_usuario") or "").strip(),
                "correo": (request.POST.get("correo") or "").strip(),
                "contrasena": (request.POST.get("contrasena") or "").strip(),
            },
            context={"usuario_id": usuario_id},
        )
        if ser.is_valid():
            d = ser.validated_data
            serv.actualizar_perfil_cliente(
                usuario_id=usuario_id,
                nombre_usuario=d["nombre_usuario"],
                correo=d["correo"],
                contrasena=d.get("contrasena") or None,
            )
            return redirect(f"{request.path}?page={page}")

    perfil = serv.obtener_perfil_cliente(usuario_id) or {}
    filas, total_pages = repo.compras_cliente(usuario_id, page, PER_PAGE)

    return render(request, "users/PerfilCliente.html", {
        "perfil": perfil,
        "errors": (locals().get("ser") and getattr(ser, "errors", None)) or None,
        "filas": filas,
        "page": page,
        "total_pages": total_pages,
    })
