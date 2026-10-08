from django import template

register = template.Library()


@register.filter
def nombre_persona(usuario):
    perfil = getattr(usuario, 'perfil', None)
    if perfil and perfil.nombre:
        return perfil.nombre
    return usuario.get_username()
