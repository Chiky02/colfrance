from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AlertaForm, CancelacionForm, ParadaForm
from .models import Alerta, Parada
from .roles import DESCRIPCIONES, ETIQUETAS, rol_de


def prohibido():
    return HttpResponseForbidden(
        'No tiene permiso para esta acción.',
        content_type='text/plain; charset=utf-8',
    )


def consulta(user, rol):
    if rol == 'operario':
        alertas = Alerta.objects.filter(usuario=user)
        paradas = Parada.objects.none()
    elif rol in ('supervisor', 'jefe'):
        alertas = Alerta.objects.all()
        paradas = Parada.objects.all()
    else:
        alertas = Alerta.objects.none()
        paradas = Parada.objects.none()
    return (
        alertas.select_related('usuario'),
        paradas.select_related('usuario', 'cancelada_por'),
    )


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
                return redirect('principal')
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
                return redirect('principal')
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

    alertas, paradas = consulta(request.user, rol)
    edicion = []
    for alerta in alertas:
        if rol == 'supervisor':
            formulario = editar_errores.get(alerta.pk) or AlertaForm(
                instance=alerta,
                prefix=f'editar-{alerta.pk}',
            )
        else:
            formulario = None
        edicion.append((alerta, formulario))

    listado_paradas = []
    for parada in paradas:
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
            'edicion': edicion,
            'listado_paradas': listado_paradas,
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
            return redirect('principal')
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
    return redirect('principal')
