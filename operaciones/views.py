from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import AlertaForm, CancelacionForm, ParadaForm
from .models import Alerta, Parada
from .roles import DESCRIPCIONES, ETIQUETAS, rol_de

POR_PAGINA = 5
User = get_user_model()


def prohibido():
    return HttpResponseForbidden(
        'No tiene permiso para esta acción.',
        content_type='text/plain; charset=utf-8',
    )


def parametros(request):
    origen = request.POST if request.method == 'POST' else request.GET
    vista = origen.get('vista', 'alertas')
    if vista not in ('alertas', 'paradas'):
        vista = 'alertas'
    orden = origen.get('orden', 'reciente')
    if orden not in ('reciente', 'antiguo'):
        orden = 'reciente'
    persona = origen.get('persona', '')
    if not str(persona).isdigit():
        persona = ''
    return vista, orden, persona


def consulta(user, rol, persona, orden):
    if rol == 'operario':
        alertas = Alerta.objects.filter(usuario=user)
        paradas = Parada.objects.none()
    elif rol in ('supervisor', 'jefe'):
        alertas = Alerta.objects.all()
        paradas = Parada.objects.all()
        if persona:
            alertas = alertas.filter(usuario_id=persona)
            paradas = paradas.filter(usuario_id=persona)
    else:
        alertas = Alerta.objects.none()
        paradas = Parada.objects.none()
    if orden == 'antiguo':
        alertas = alertas.order_by('fecha', 'pk')
        paradas = paradas.order_by('inicio', 'pk')
    else:
        alertas = alertas.order_by('-fecha', '-pk')
        paradas = paradas.order_by('-inicio', '-pk')
    return (
        alertas.select_related('usuario__perfil'),
        paradas.select_related('usuario__perfil', 'cancelada_por__perfil'),
    )


def redirigir_lista(request, vista):
    _, orden, persona = parametros(request)
    consulta_url = urlencode({'vista': vista, 'persona': persona, 'orden': orden})
    return redirect(f"{reverse('principal')}?{consulta_url}")


def numero_pagina(request, clave):
    origen = request.POST if request.method == 'POST' else request.GET
    try:
        return max(int(origen.get(clave, 1)), 1)
    except (TypeError, ValueError):
        return 1


def paginar(queryset, numero):
    paginador = Paginator(queryset, POR_PAGINA)
    if numero > paginador.num_pages:
        numero = paginador.num_pages or 1
    return paginador.page(numero)


@login_required
def principal(request):
    rol = rol_de(request.user)
    alerta_form = AlertaForm(prefix='nueva')
    parada_form = ParadaForm(prefix='nueva')
    editar_errores = {}
    cancelar_errores = {}
    estado = 200

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear_alerta':
            if rol != 'operario':
                return prohibido()
            alerta_form = AlertaForm(request.POST, prefix='nueva')
            if alerta_form.is_valid():
                alerta = alerta_form.save(commit=False)
                alerta.usuario = request.user
                alerta.save()
                messages.success(request, 'Alerta registrada.')
                return redirect('principal')
            estado = 400
        elif accion == 'editar_alerta':
            if rol != 'supervisor':
                return prohibido()
            alerta = get_object_or_404(Alerta, pk=request.POST.get('alerta_id'))
            formulario = AlertaForm(
                request.POST,
                instance=alerta,
                prefix=f'editar-{alerta.pk}',
            )
            if formulario.is_valid():
                formulario.save()
                messages.success(request, 'Alerta actualizada.')
                return redirigir_lista(request, 'alertas')
            editar_errores[alerta.pk] = formulario
            estado = 400
        elif accion == 'crear_parada':
            if rol != 'supervisor':
                return prohibido()
            parada_form = ParadaForm(request.POST, prefix='nueva')
            if parada_form.is_valid():
                parada = parada_form.save(commit=False)
                parada.usuario = request.user
                parada.save()
                messages.success(request, 'Parada registrada.')
                return redirigir_lista(request, 'paradas')
            estado = 400
        elif accion == 'cancelar_parada':
            if rol != 'jefe':
                return prohibido()
            respuesta = cancelar(request)
            if respuesta is not None:
                return respuesta
            parada_id = request.POST.get('parada_id')
            if parada_id and parada_id.isdigit():
                cancelar_errores[int(parada_id)] = CancelacionForm(
                    request.POST,
                    prefix=f'cancelar-{parada_id}',
                )
            estado = 400
        else:
            return prohibido()

    vista, orden, persona = parametros(request)
    if rol == 'operario':
        vista = 'alertas'
    alertas, paradas = consulta(request.user, rol, persona, orden)
    personas = []
    if rol in ('supervisor', 'jefe'):
        personas = User.objects.filter(perfil__isnull=False).select_related('perfil').order_by(
            'perfil__nombre'
        )
    pagina_alertas = paginar(alertas, numero_pagina(request, 'alertas'))
    pagina_paradas = paginar(paradas, numero_pagina(request, 'paradas'))
    edicion = []
    for alerta in pagina_alertas:
        if rol == 'supervisor':
            formulario = editar_errores.get(alerta.pk) or AlertaForm(
                instance=alerta,
                prefix=f'editar-{alerta.pk}',
            )
        else:
            formulario = None
        edicion.append((alerta, formulario))

    listado_paradas = []
    for parada in pagina_paradas:
        if rol == 'jefe' and parada.cancelada_en is None:
            formulario = cancelar_errores.get(parada.pk) or CancelacionForm(
                prefix=f'cancelar-{parada.pk}',
            )
        else:
            formulario = None
        listado_paradas.append((parada, formulario))

    return render(
        request,
        'operaciones/principal.html',
        {
            'rol': rol,
            'rol_etiqueta': ETIQUETAS.get(rol, 'Sin rol'),
            'rol_descripcion': DESCRIPCIONES.get(rol, 'Esta cuenta no tiene un rol asignado.'),
            'alerta_form': alerta_form,
            'parada_form': parada_form,
            'perfil': getattr(request.user, 'perfil', None),
            'edicion': edicion,
            'listado_paradas': listado_paradas,
            'pagina_alertas': pagina_alertas,
            'pagina_paradas': pagina_paradas,
            'vista': vista,
            'orden': orden,
            'persona': persona,
            'personas': personas,
        },
        status=estado,
    )


def cancelar(request):
    parada_id = request.POST.get('parada_id')
    if not (parada_id or '').isdigit():
        raise Http404('Parada no encontrada.')
    with transaction.atomic():
        parada = get_object_or_404(
            Parada.objects.select_for_update(),
            pk=parada_id,
        )
        if parada.cancelada_en is not None:
            messages.error(
                request,
                'Esta parada ya estaba cancelada. Se conservó el primer registro.',
            )
            return redirigir_lista(request, 'paradas')
        formulario = CancelacionForm(request.POST, prefix=f'cancelar-{parada.pk}')
        if not formulario.is_valid():
            return None
        parada.cancelada_por = request.user
        parada.cancelada_en = timezone.now()
        parada.motivo_cancelacion = formulario.cleaned_data['motivo_cancelacion']
        parada.save(
            update_fields=['cancelada_por', 'cancelada_en', 'motivo_cancelacion']
        )
    messages.success(request, 'Parada cancelada.')
    return redirigir_lista(request, 'paradas')
