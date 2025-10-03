from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator



class Usuario(models.Model):
    id_usuario = models.BigAutoField(primary_key=True, db_column='id_usuario')
    correo = models.CharField(max_length=50, db_column='correo')
    nombre_usuario = models.CharField(max_length=10, db_column='nombre_usuario')
    contrasena = models.CharField(max_length=128, db_column='contrasena')

    class Meta:
        db_table = '"USUARIO"'
        managed = True
        constraints = [
            models.UniqueConstraint(
                fields=['nombre_usuario', 'correo'],
                name='UQ_CONSTRAIN'
            )
        ]
        indexes = [
            models.Index(fields=['correo'], name='ix_usuario_correo'),
            models.Index(fields=['nombre_usuario'], name='ix_usuario_nombre'),
        ]

    def __str__(self):
        return f'{self.nombre_usuario} <{self.correo}>'


class Administrador(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        primary_key=True,
        db_column='id_usuario',
        related_name='administrador'
    )
    acceso = models.BooleanField(db_column='acceso', default=True)

    class Meta:
        db_table = '"ADMINISTRADOR"'
        managed = True

    def __str__(self):
        return f'Administrador #{self.usuario_id}'


class Cliente(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        primary_key=True,
        db_column='id_usuario',
        related_name='cliente'
    )
    excliente = models.BooleanField(db_column='excliente', default=False)
    fecha_creacion = models.DateTimeField(db_column='fecha_creacion', auto_now_add=True)
    saldo = models.DecimalField(
        db_column='saldo',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )

    class Meta:
        db_table = '"CLIENTE"'
        managed = True
        constraints = [
            models.CheckConstraint(check=models.Q(saldo__gte=0), name='CHECK_SALDO'),
        ]
        indexes = [
            models.Index(fields=['saldo'], name='ix_cliente_saldo'),
        ]

    def __str__(self):
        estado = 'excliente' if self.excliente else 'activo'
        return f'Cliente #{self.usuario_id} ({estado})'



class Autor(models.Model):
    id_autor = models.BigAutoField(primary_key=True, db_column='id_autor')
    nombre = models.CharField(max_length=50, db_column='nombre')

    class Meta:
        db_table = '"AUTOR"'
        managed = True
        constraints = [
            models.UniqueConstraint(fields=['nombre'], name='UQ_AUTOR_NOMBRE')
        ]

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    id_categoria = models.BigAutoField(primary_key=True, db_column='id_categoria')
    fecha = models.DateTimeField(db_column='fecha', auto_now_add=True)  # DEFAULT now()
    nombre = models.CharField(max_length=50, db_column='nombre')
    descripcion = models.TextField(null=True, blank=True, db_column='descripcion')

    class Meta:
        db_table = '"CATEGORIA"'
        managed = True
        indexes = [
            models.Index(fields=['nombre'], name='ix_categoria_nombre'),
        ]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    id_producto = models.BigAutoField(primary_key=True, db_column='id_producto')
    nombre = models.CharField(max_length=50, db_column='nombre')
    fecha = models.DateTimeField(db_column='fecha', auto_now_add=True)  # DEFAULT now()
    archivo = models.BinaryField(db_column='archivo')
    activo = models.BooleanField(db_column='activo', default=True)
    categoria = models.ForeignKey(
        Categoria,
        db_column='id_categoria',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='productos',
    )
    autor = models.ForeignKey(
        'Autor',
        db_column='id_autor',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='productos',
    )

    class Meta:
        db_table = '"PRODUCTO"'
        managed = True
        indexes = [
            models.Index(fields=['nombre'], name='ix_producto_nombre'),
            models.Index(fields=['activo'], name='ix_producto_activo'),
        ]

    def __str__(self):
        return f'{self.id_producto} - {self.nombre}'


class ImagenProducto(models.Model):
    id_imagen_producto = models.BigAutoField(primary_key=True, db_column='id_imagen_producto')
    orden = models.IntegerField(db_column='orden')
    archivo = models.BinaryField(db_column='archivo')
    producto = models.ForeignKey(
        Producto,
        db_column='id_producto',
        on_delete=models.CASCADE,
        related_name='imagenes'
    )

    class Meta:
        db_table = '"IMAGEN_PRODUCTO"'
        managed = True
        ordering = ['orden']
        indexes = [
            models.Index(fields=['producto', 'orden'], name='ix_img_prod_orden'),
        ]

    def __str__(self):
        return f'Img {self.id_imagen_producto} (P{self.producto_id}, orden {self.orden})'


class DetallesProducto(models.Model):
    producto = models.OneToOneField(
        Producto,
        primary_key=True,
        db_column='id_producto',
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    precio = models.DecimalField(db_column='precio', max_digits=12, decimal_places=2)
    version = models.CharField(db_column='version', max_length=50, null=True, blank=True)
    descripcion = models.TextField(db_column='descripcion', null=True, blank=True)

    class Meta:
        db_table = '"DETALLES_PRODUCTO"'
        managed = True
        constraints = [
            models.CheckConstraint(check=models.Q(precio__gte=0), name='CHECK_PRECIO'),
        ]
        indexes = [
            models.Index(fields=['precio'], name='ix_det_precio'),
        ]

    def __str__(self):
        return f'Detalles P{self.producto_id}'



class CalificacionProducto(models.Model):
    # Django no soporta PK compuesta; se fija PK en id_producto y se asegura (id_producto, id_usuario) en constrains.
    producto = models.ForeignKey(
        Producto,
        db_column='id_producto',
        on_delete=models.PROTECT,
        related_name='calificaciones',
        primary_key=True,
    )
    usuario = models.ForeignKey(
        'Cliente',
        db_column='id_usuario',
        on_delete=models.PROTECT,
        related_name='calificaciones'
    )
    calificacion = models.IntegerField(
        db_column='calificacion',
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    fecha = models.DateTimeField(db_column='fecha', auto_now_add=True)

    class Meta:
        db_table = '"CALIFICACION_PRODUCTO"'
        managed = True
        constraints = [
            models.CheckConstraint(
                check=models.Q(calificacion__gte=1) & models.Q(calificacion__lte=5),
                name='CHECK_CALIFICACION'
            ),
            models.UniqueConstraint(
                fields=['producto', 'usuario'],
                name='PK_CALIFICACION_PRODUCTO'
            ),
        ]
        indexes = [
            models.Index(fields=['usuario'], name='ix_calif_usuario'),
        ]

    def __str__(self):
        return f'Calif P{self.producto_id} U{self.usuario_id} = {self.calificacion}'


class ComentarioProducto(models.Model):
    id_comentario_producto = models.BigAutoField(primary_key=True, db_column='id_comentario_producto')
    descripcion = models.TextField(db_column='descripcion')
    fecha = models.DateTimeField(db_column='fecha', auto_now_add=True)
    producto = models.ForeignKey(
        Producto,
        db_column='id_producto',
        on_delete=models.PROTECT,
        related_name='comentarios'
    )
    usuario = models.ForeignKey(
        'Cliente',
        db_column='id_usuario',
        on_delete=models.PROTECT,
        related_name='comentarios'
    )

    class Meta:
        db_table = '"COMENTARIO_PRODUCTO"'
        managed = True
        indexes = [
            models.Index(fields=['producto'], name='ix_comentario_producto'),
            models.Index(fields=['usuario'], name='ix_comentario_usuario'),
            models.Index(fields=['fecha'], name='ix_comentario_fecha'),
        ]

    def __str__(self):
        return f'Comentario #{self.id_comentario_producto} (P{self.producto_id})'


class CompraProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        db_column='id_producto',
        on_delete=models.PROTECT,
        related_name='compras',
        primary_key=True,
    )
    usuario = models.ForeignKey(
        'Cliente',
        db_column='id_usuario',
        on_delete=models.PROTECT,
        related_name='compras'
    )
    fecha = models.DateTimeField(db_column='fecha', auto_now_add=True)

    class Meta:
        db_table = '"COMPRA_PRODUCTO"'
        managed = True
        constraints = [
            models.UniqueConstraint(
                fields=['producto', 'usuario'],
                name='PK_COMPRA_PRODUCTO'
            ),
        ]
        indexes = [
            models.Index(fields=['usuario'], name='ix_compra_usuario'),
            models.Index(fields=['fecha'], name='ix_compra_fecha'),
        ]

    def __str__(self):
        return f'Compra P{self.producto_id} U{self.usuario_id}'

