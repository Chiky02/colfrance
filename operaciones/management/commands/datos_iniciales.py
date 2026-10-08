from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from operaciones.models import Perfil

USUARIOS = (
    ('operarios@test.com', 'operario123', 'operario', 'operario', 'Ana Pérez', '3001112233', '1010101010'),
    ('operarios2@test.com', 'operario123', 'operario', 'operario2', 'Luis Gómez', '3002223344', '2020202020'),
    ('supervisor@test.com', 'supervisor123', 'supervisor', 'supervisor', 'Marta Ruiz', '3003334455', '3030303030'),
    ('jefe@test.com', 'jefe12345', 'jefe', 'jefe', 'Carlos Díaz', '3004445566', '4040404040'),
)


class Command(BaseCommand):
    help = 'Crea los grupos y un usuario de demostración por rol, más un segundo operario.'

    def handle(self, *args, **options):
        grupos = {
            nombre: Group.objects.get_or_create(name=nombre)[0]
            for nombre in ('operario', 'supervisor', 'jefe')
        }
        for correo, password, rol, anterior, nombre, telefono, cedula in USUARIOS:
            try:
                validate_email(correo)
            except ValidationError as exc:
                raise CommandError(f'{correo} no es un correo válido.') from exc
            if User.objects.filter(username=correo).exists():
                usuario = User.objects.get(username=correo)
            elif User.objects.filter(username=anterior).exists():
                usuario = User.objects.get(username=anterior)
                usuario.username = correo
            else:
                usuario = User(username=correo)
            usuario.email = correo
            usuario.set_password(password)
            usuario.is_active = True
            usuario.save()
            usuario.groups.set([grupos[rol]])
            Perfil.objects.update_or_create(
                usuario=usuario,
                defaults={'nombre': nombre, 'telefono': telefono, 'cedula': cedula},
            )
            self.stdout.write(f'{correo} ({rol}) {nombre}')
        self.stdout.write(self.style.SUCCESS('Datos iniciales listos.'))
