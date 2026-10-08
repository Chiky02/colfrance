from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

USUARIOS = (
    ('operarios@test.com', 'operario123', 'operario', 'operario'),
    ('operarios2@test.com', 'operario123', 'operario', 'operario2'),
    ('supervisor@test.com', 'supervisor123', 'supervisor', 'supervisor'),
    ('jefe@test.com', 'jefe12345', 'jefe', 'jefe'),
)


class Command(BaseCommand):
    help = 'Crea los grupos y un usuario de demostración por rol, más un segundo operario.'

    def handle(self, *args, **options):
        grupos = {
            nombre: Group.objects.get_or_create(name=nombre)[0]
            for nombre in ('operario', 'supervisor', 'jefe')
        }
        for correo, password, rol, anterior in USUARIOS:
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
            self.stdout.write(f'{correo} ({rol})')
        self.stdout.write(self.style.SUCCESS('Datos iniciales listos.'))
