from django.contrib import admin
from django import forms
from django.utils.html import format_html

from core.models import (
    Autor,
    Categoria,
    Producto,
    DetallesProducto,
    ImagenProducto,
    CalificacionProducto,
    ComentarioProducto,
    CompraProducto,
)

# =========================
# Forms para BinaryField(s)
# =========================

class ProductoAdminForm(forms.ModelForm):
    # Campo de archivo opcional para SOBREESCRIBIR el BinaryField 'archivo'
    archivo_file = forms.FileField(required=False, label="Archivo (sobrescribe bytea)")

    class Meta:
        model = Producto
        # IMPORTANTE: NO incluir 'archivo' (BinaryField no editable)
        fields = ['nombre', 'activo', 'categoria', 'autor', 'archivo_file']

    def save(self, commit=True):
        obj = super().save(commit=False)
        f = self.cleaned_data.get('archivo_file')
        if f:
            obj.archivo = f.read()  # Guardar bytes en el BinaryField
        if commit:
            obj.save()
        return obj


class ImagenProductoAdminForm(forms.ModelForm):
    archivo_file = forms.FileField(required=False, label="Imagen (sobrescribe bytea)")

    class Meta:
        model = ImagenProducto
        # NO incluir 'archivo' (BinaryField no editable)
        fields = ['producto', 'orden', 'archivo_file']

    def save(self, commit=True):
        obj = super().save(commit=False)
        f = self.cleaned_data.get('archivo_file')
        if f:
            obj.archivo = f.read()
        if commit:
            obj.save()
        return obj


# =========================
# Inlines
# =========================

class DetallesProductoInline(admin.StackedInline):
    model = DetallesProducto
    can_delete = False
    extra = 0
    fk_name = 'producto'
    fields = ('precio', 'version', 'descripcion')


# ===============
# ModelAdmins
# ===============

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('id_autor', 'nombre')
    search_fields = ('nombre',)
    ordering = ('id_autor',)
    list_per_page = 25


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id_categoria', 'nombre', 'fecha', 'descripcion_corta')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('fecha',)
    ordering = ('-fecha', '-id_categoria')
    date_hierarchy = 'fecha'
    list_per_page = 25

    @admin.display(description='Descripción (30)')
    def descripcion_corta(self, obj):
        if not obj.descripcion:
            return ''
        return (obj.descripcion[:30] + '…') if len(obj.descripcion) > 30 else obj.descripcion


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoAdminForm
    inlines = [DetallesProductoInline]

    readonly_fields = ('id_producto', 'fecha', 'archivo_len')

    list_display = ('id_producto', 'nombre', 'autor', 'categoria', 'activo', 'fecha', 'archivo_len')
    list_filter = ('activo', 'categoria', 'autor', 'fecha')
    search_fields = ('nombre', 'autor__nombre', 'categoria__nombre')
    ordering = ('-fecha', '-id_producto')
    date_hierarchy = 'fecha'
    list_per_page = 25
    raw_id_fields = ('categoria', 'autor')

    fieldsets = (
        ('Identificación', {
            'fields': ('id_producto', 'fecha')
        }),
        ('Datos principales', {
            'fields': ('nombre', 'activo', 'categoria', 'autor')
        }),
        ('Archivo', {
            # NO incluir 'archivo' aquí; solo mostramos tamaño + upload
            'fields': ('archivo_len', 'archivo_file'),
            'description': "Sube un archivo para reemplazar el contenido del campo bytea."
        }),
    )

    @admin.display(description='Tamaño archivo (bytes)')
    def archivo_len(self, obj):
        try:
            return len(obj.archivo) if obj.archivo else 0
        except TypeError:
            return 0

    actions = ['marcar_activo', 'marcar_inactivo']

    @admin.action(description='Marcar seleccionados como ACTIVO')
    def marcar_activo(self, request, queryset):
        queryset.update(activo=True)

    @admin.action(description='Marcar seleccionados como INACTIVO')
    def marcar_inactivo(self, request, queryset):
        queryset.update(activo=False)


@admin.register(ImagenProducto)
class ImagenProductoAdmin(admin.ModelAdmin):
    form = ImagenProductoAdminForm

    readonly_fields = ('id_imagen_producto', 'archivo_len', 'preview_info')
    list_display = ('id_imagen_producto', 'producto', 'orden', 'archivo_len')
    list_filter = ('producto',)
    search_fields = ('producto__nombre',)
    ordering = ('producto', 'orden', 'id_imagen_producto')
    list_per_page = 25
    raw_id_fields = ('producto',)

    # NO incluir 'archivo' en fields; solo el file uploader
    fields = (
        'id_imagen_producto',
        'producto',
        'orden',
        'archivo_len',
        'archivo_file',
        'preview_info',
    )

    @admin.display(description='Tamaño archivo (bytes)')
    def archivo_len(self, obj):
        try:
            return len(obj.archivo) if obj.archivo else 0
        except TypeError:
            return 0

    @admin.display(description='Preview/Info')
    def preview_info(self, obj):
        size = self.archivo_len(obj)
        return format_html("<small>Imagen almacenada ({} bytes). Para reemplazar, usa el campo de archivo.</small>", size)


@admin.register(DetallesProducto)
class DetallesProductoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'precio', 'version', 'descripcion_corta')
    search_fields = ('producto__nombre', 'version', 'descripcion')
    list_filter = ('precio',)
    ordering = ('producto',)
    list_per_page = 25
    raw_id_fields = ('producto',)

    @admin.display(description='Descripción (30)')
    def descripcion_corta(self, obj):
        if not obj.descripcion:
            return ''
        return (obj.descripcion[:30] + '…') if len(obj.descripcion) > 30 else obj.descripcion


@admin.register(CalificacionProducto)
class CalificacionProductoAdmin(admin.ModelAdmin):
    readonly_fields = ('fecha',)
    list_display = ('producto', 'usuario', 'calificacion', 'fecha')
    list_filter = ('calificacion', 'fecha')
    search_fields = ('producto__nombre', 'usuario__usuario__nombre_usuario', 'usuario__usuario__correo')
    ordering = ('-fecha', 'producto', 'usuario')
    date_hierarchy = 'fecha'
    list_per_page = 25
    raw_id_fields = ('producto', 'usuario')


@admin.register(ComentarioProducto)
class ComentarioProductoAdmin(admin.ModelAdmin):
    readonly_fields = ('id_comentario_producto', 'fecha')
    list_display = ('id_comentario_producto', 'producto', 'usuario', 'fecha', 'descripcion_corta')
    list_filter = ('fecha',)
    search_fields = ('descripcion', 'producto__nombre', 'usuario__usuario__nombre_usuario', 'usuario__usuario__correo')
    ordering = ('-fecha', '-id_comentario_producto')
    date_hierarchy = 'fecha'
    list_per_page = 25
    raw_id_fields = ('producto', 'usuario')

    @admin.display(description='Descripción (50)')
    def descripcion_corta(self, obj):
        return (obj.descripcion[:50] + '…') if len(obj.descripcion) > 50 else obj.descripcion


@admin.register(CompraProducto)
class CompraProductoAdmin(admin.ModelAdmin):
    readonly_fields = ('fecha',)
    list_display = ('producto', 'usuario', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('producto__nombre', 'usuario__usuario__nombre_usuario', 'usuario__usuario__correo')
    ordering = ('-fecha', 'producto', 'usuario')
    date_hierarchy = 'fecha'
    list_per_page = 25
    raw_id_fields = ('producto', 'usuario')
