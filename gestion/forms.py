from django import forms
from .models import Paciente
from .models import Cita
from .models import DienteEstado

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nombre', 'cedula', 'fecha_nacimiento', 'telefono', 'email', 'alergias', 'diabetes', 'hipertension', 'notas_medicas']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            # Puedes añadir más clases de Bootstrap aquí
        }

class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['paciente', 'tratamiento', 'fecha', 'hora', 'motivo', 'observaciones_doctor']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'paciente': forms.Select(attrs={'class': 'form-select'}),
            'tratamiento': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones_doctor': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DienteEstadoForm(forms.ModelForm):
    class Meta:
        model = DienteEstado
        fields = ['diente', 'estado', 'notas']
        widgets = {
            'diente': forms.NumberInput(attrs={'class': 'form-control', 'min': 11, 'max': 85}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Cara vestibular'}),
        }