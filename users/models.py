from django.db import models
from django.core.validators import MinValueValidator

# managed = Permite a Django la gestion de la base de datos (CREATE, DROP, UPDATE)

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
