from django import forms
from .models import Paciente, Cita, DienteEstado, Tratamiento, Pago, ArchivoPaciente

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

class TratamientoForm(forms.ModelForm):
    class Meta:
        model = Tratamiento
        # Asumo que tus campos se llaman así por lo que usamos en el Dashboard
        fields = ['nombre', 'costo_base']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Limpieza Dental'}),
            'costo_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['monto', 'notas']
        widgets = {
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notas': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Transferencia #1234, Abono efectivo...'}),
        }

class ArchivoPacienteForm(forms.ModelForm):
    class Meta:
        model = ArchivoPaciente
        fields = ['titulo', 'archivo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }