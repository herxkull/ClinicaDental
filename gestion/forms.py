from django import forms
from .models import Paciente

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