from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Alerta, Parada

ENTRADA_FECHA = '%Y-%m-%dT%H:%M'


class EntradaForm(AuthenticationForm):
    username = forms.EmailField(
        label='Correo',
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'placeholder': 'operarios@test.com',
        }),
        error_messages={
            'required': 'Ingrese el correo.',
            'invalid': 'Ingrese un correo válido, por ejemplo operarios@test.com.',
        },
    )
    error_messages = {
        'invalid_login': 'Correo o contraseña incorrectos.',
        'inactive': 'Esta cuenta está inactiva.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].label = 'Contraseña'


def texto_obligatorio(valor, mensaje):
    limpio = valor.strip()
    if not limpio:
        raise forms.ValidationError(mensaje)
    return limpio


class AlertaForm(forms.ModelForm):
    class Meta:
        model = Alerta
        fields = ['maquina', 'descripcion']
        labels = {
            'maquina': 'Máquina',
            'descripcion': 'Descripción',
        }
        widgets = {
            'maquina': forms.TextInput(attrs={'placeholder': 'Ej. Prensa 1'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Qué ocurrió'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['maquina'].error_messages['required'] = 'Indique la máquina.'
        self.fields['descripcion'].error_messages['required'] = (
            'La descripción no puede estar vacía.'
        )

    def clean_maquina(self):
        return texto_obligatorio(self.cleaned_data['maquina'], 'Indique la máquina.')

    def clean_descripcion(self):
        return texto_obligatorio(
            self.cleaned_data['descripcion'],
            'La descripción no puede estar vacía.',
        )


class ParadaForm(forms.ModelForm):
    class Meta:
        model = Parada
        fields = ['maquina', 'inicio', 'fin', 'motivo']
        labels = {
            'maquina': 'Máquina',
            'inicio': 'Inicio',
            'fin': 'Finalización',
            'motivo': 'Motivo',
        }
        widgets = {
            'maquina': forms.TextInput(attrs={'placeholder': 'Ej. Prensa 1'}),
            'inicio': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format=ENTRADA_FECHA,
            ),
            'fin': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format=ENTRADA_FECHA,
            ),
            'motivo': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Por qué se detuvo'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['maquina'].error_messages['required'] = 'Indique la máquina.'
        self.fields['motivo'].error_messages['required'] = 'El motivo no puede estar vacío.'
        self.fields['inicio'].error_messages['required'] = 'Indique el inicio.'
        self.fields['fin'].error_messages['required'] = 'Indique la finalización.'
        for nombre in ('inicio', 'fin'):
            self.fields[nombre].input_formats = [ENTRADA_FECHA, '%Y-%m-%dT%H:%M:%S']

    def clean_maquina(self):
        return texto_obligatorio(self.cleaned_data['maquina'], 'Indique la máquina.')

    def clean_motivo(self):
        return texto_obligatorio(
            self.cleaned_data['motivo'],
            'El motivo no puede estar vacío.',
        )

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('inicio')
        fin = cleaned.get('fin')
        if inicio and fin and fin <= inicio:
            self.add_error('fin', 'La finalización debe ser posterior al inicio.')
        return cleaned


class CancelacionForm(forms.Form):
    motivo_cancelacion = forms.CharField(
        label='Motivo de la cancelación',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Por qué se cancela'}),
        error_messages={'required': 'El motivo no puede estar vacío.'},
    )

    def clean_motivo_cancelacion(self):
        return texto_obligatorio(
            self.cleaned_data['motivo_cancelacion'],
            'El motivo no puede estar vacío.',
        )
