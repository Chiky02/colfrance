ROLES = ('operario', 'supervisor', 'jefe')

ETIQUETAS = {
    'operario': 'Operario',
    'supervisor': 'Supervisor',
    'jefe': 'Jefe',
}

DESCRIPCIONES = {
    'operario': 'Registra alertas y consulta solo las que usted reportó.',
    'supervisor': 'Consulta y edita alertas, y registra paradas.',
    'jefe': 'Consulta alertas y paradas, y cancela paradas indicando un motivo.',
}


def rol_de(user):
    if not getattr(user, 'is_authenticated', False):
        return None
    nombres = set(user.groups.values_list('name', flat=True))
    for nombre in ROLES:
        if nombre in nombres:
            return nombre
    return None
