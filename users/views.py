from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from rest_framework import serializers

from . import serializer as serial


@require_http_methods(["GET", "POST"])
def iniciar_sesion_view(request):
    ctx = {"errors": None}
    if request.method == "POST":
        ser = serial.IniciarSesionSerializer(data={
            "nombre": request.POST.get("nombre", "").strip(),
            "contrasena": request.POST.get("contrasena", ""),
        })
        if ser.is_valid():
            usuario = ser.validated_data["usuario"]
            tipo = ser.validated_data["tipo"]

            # Guardar sesión mínima (no usamos auth.User)
            request.session["usuario_id"] = usuario.id_usuario
            request.session["usuario_nombre"] = usuario.nombre_usuario
            request.session["usuario_correo"] = usuario.correo
            request.session["usuario_contrasena"] = usuario.contrasena
            request.session["usuario_tipo"] = tipo

            return redirect("users:perfil_admin" if tipo == "administrador" else "users:catalogo")

        ctx["errors"] = ser.errors

    return render(request, "users/IniciarSesion.html", ctx)


@require_http_methods(["GET", "POST"])
def registrarse_view(request):
    # Formulario HTML para registrarse.
    # - POST crea Usuario y siempre su Cliente asociado.
    # - Si OK: inicia sesión y redirige a Catalogo.

    ctx = {"errors": None}
    if request.method == "POST":
        ser = serial.RegistrarseSerializer(data={
            "nombre": request.POST.get("nombre", "").strip(),
            "correo": request.POST.get("correo", "").strip(),
            "contrasena": request.POST.get("contrasena", ""),
        })
        try:
            ser.is_valid(raise_exception=True)
            usuario = ser.save()
            request.session["usuario_id"] = usuario.id_usuario
            request.session["usuario_tipo"] = "cliente"
            request.session["usuario_nombre"] = usuario.nombre_usuario
            request.session["usuario_correo"] = usuario.correo
            request.session["usuario_contrasena"] = usuario.contrasena
            return redirect("users:catalogo")
        except serializers.ValidationError as e:
            ctx["errors"] = e.detail

    return render(request, "users/Registrarse.html", ctx)

def perfil_admin_view(request):

    if request.session.get("usuario_tipo") != "administrador": # Par que el cliente no acceda a administrador por URL xd
        return redirect("users:iniciar")

    ctx = {
        "errors": None,
        "success": None
    }

    if request.method == "POST":
        data = {
            "nombre": (request.POST.get("nombre") or "").strip(),
            "correo": (request.POST.get("correo") or "").strip(),
            "contrasena": (request.POST.get("contrasena") or "").strip(),
        }
        ser = serial.AdminPerfilUpdateSerializer(data=data, context={"request": request})
        print(data)
        try:
            ser.is_valid(raise_exception=True)
            usuario = ser.save()

            request.session["usuario_nombre"] = usuario.nombre_usuario
            request.session["usuario_correo"] = usuario.correo
            request.session["usuario_contrasena"] = usuario.contrasena
            ctx["success"] = "Datos actualizados correctamente."
        except serializers.ValidationError as e:
            ctx["errors"] = e.detail

    return render(request, "users/PerfilAdministrador.html", ctx)


def logout_view(request):
    request.session.flush()  # limpia toda la sesión
    return redirect("users:iniciar")

def catalogo_view(request):
    return render(request, "users/Catalogo.html")
