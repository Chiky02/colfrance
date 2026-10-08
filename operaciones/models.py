from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q

cedula_valida = RegexValidator(
    r'^\d{6,12}$',
    'La cédula debe tener entre 6 y 12 dígitos.',
)
telefono_valido = RegexValidator(
    r'^\d{7,15}$',
    'El teléfono debe tener entre 7 y 15 dígitos.',
)


class Perfil(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
    )
    nombre = models.CharField('nombre', max_length=120)
    telefono = models.CharField('teléfono', max_length=15, validators=[telefono_valido])
    cedula = models.CharField(
        'cédula',
        max_length=12,
        unique=True,
        validators=[cedula_valida],
    )

    class Meta:
        verbose_name = 'perfil'
        verbose_name_plural = 'perfiles'

    def __str__(self):
        return self.nombre


class Alerta(models.Model):
    maquina = models.CharField('máquina', max_length=100)
    descripcion = models.TextField('descripción')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='alertas',
        verbose_name='usuario',
    )
    fecha = models.DateTimeField('fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'alerta'
        verbose_name_plural = 'alertas'
        ordering = ['-fecha', '-pk']

    def __str__(self):
        return f'{self.maquina}: {self.descripcion[:40]}'


class Parada(models.Model):
    maquina = models.CharField('máquina', max_length=100)
    inicio = models.DateTimeField('inicio')
    fin = models.DateTimeField('finalización')
    motivo = models.TextField('motivo')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='paradas',
        verbose_name='usuario',
    )
    cancelada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='paradas_canceladas',
        verbose_name='cancelada por',
    )
    cancelada_en = models.DateTimeField('cancelada en', null=True, blank=True)
    motivo_cancelacion = models.TextField('motivo de cancelación', null=True, blank=True)

    class Meta:
        verbose_name = 'parada'
        verbose_name_plural = 'paradas'
        ordering = ['-inicio', '-pk']
        constraints = [
            models.CheckConstraint(
                condition=Q(fin__gt=F('inicio')),
                name='parada_fin_posterior_al_inicio',
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        cancelada_por__isnull=True,
                        cancelada_en__isnull=True,
                        motivo_cancelacion__isnull=True,
                    )
                    | Q(
                        cancelada_por__isnull=False,
                        cancelada_en__isnull=False,
                        motivo_cancelacion__isnull=False,
                    )
                ),
                name='parada_cancelacion_completa_o_vacia',
            ),
        ]

    def __str__(self):
        return f'{self.maquina} ({self.inicio:%d/%m/%Y %H:%M})'

    def clean(self):
        super().clean()
        campos = [self.cancelada_por_id, self.cancelada_en, self.motivo_cancelacion]
        presentes = [valor not in (None, '') for valor in campos]
        if any(presentes) and not all(presentes):
            raise ValidationError(
                'La cancelación debe indicar quién, cuándo y por qué.'
            )

    @property
    def duracion_minutos(self):
        return int(round((self.fin - self.inicio).total_seconds() / 60))
