from django import forms
from .models import Paciente, Cita, Tratamiento, Pago, ArchivoPaciente, Receta, ConfiguracionClinica

class ConfiguracionClinicaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionClinica
        fields = '__all__'
        exclude = ['horarios_atencion']
        widgets = {
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control rounded-2xl border-gray-200 focus:ring-blue-500'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control rounded-2xl border-gray-200 focus:ring-blue-500', 'rows': 2}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control rounded-2xl border-gray-200 focus:ring-blue-500'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control rounded-2xl border-gray-200 focus:ring-blue-500'}),
            'duracion_cita_estandar': forms.NumberInput(attrs={'class': 'form-control rounded-2xl border-gray-200 focus:ring-blue-500'}),
            'moneda_simbolo': forms.TextInput(attrs={'class': 'form-control rounded-2xl border-gray-200 focus:ring-blue-500'}),
            'impuesto_porcentaje': forms.NumberInput(attrs={'class': 'form-control rounded-2xl border-gray-200 focus:ring-blue-500'}),
            'pie_pagina_recibo': forms.Textarea(attrs={'class': 'form-control rounded-2xl border-gray-200 focus:ring-blue-500', 'rows': 2}),
            'whatsapp_numero': forms.TextInput(attrs={'class': 'form-control rounded-2xl border-gray-200 focus:ring-blue-500'}),
            'whatsapp_recordatorios_activos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'color_primario': forms.TextInput(attrs={'class': 'form-control rounded-2xl border-gray-200', 'type': 'color'}),
            'color_sidebar': forms.TextInput(attrs={'class': 'form-control rounded-2xl border-gray-200', 'type': 'color'}),
            'color_fondo': forms.TextInput(attrs={'class': 'form-control rounded-2xl border-gray-200', 'type': 'color'}),
            'escala_interfaz': forms.NumberInput(attrs={'class': 'form-range', 'type': 'range', 'min': '80', 'max': '120', 'step': '5'}),
            'tema_oscuro': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fuente_familia': forms.Select(attrs={'class': 'form-select rounded-2xl border-gray-200'}),
        }

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__' # o tus campos específicos
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['paciente', 'doctor', 'tratamiento', 'fecha', 'hora', 'observaciones_doctor', 'motivo']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select rounded-xl'}),
            'tratamiento': forms.Select(attrs={'class': 'form-select rounded-xl'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control rounded-xl', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control rounded-xl', 'type': 'time'}),
            'observaciones_doctor': forms.Textarea(attrs={'class': 'form-control rounded-xl', 'rows': 2}),
            'motivo': forms.TextInput(attrs={'class': 'form-control rounded-xl'}),
        }


class TratamientoForm(forms.ModelForm):
    class Meta:
        model = Tratamiento
        fields = ['nombre', 'precio_venta', 'comision_clinica_porcentaje', 'doctor_referencia', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control rounded-xl', 'placeholder': 'Ej. Limpieza Dental'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control rounded-xl', 'step': '0.01'}),
            'comision_clinica_porcentaje': forms.NumberInput(attrs={'class': 'form-control rounded-xl', 'step': '0.01'}),
            'doctor_referencia': forms.Select(attrs={'class': 'form-select rounded-xl'}),
            'color': forms.TextInput(attrs={'class': 'form-control rounded-xl', 'type': 'color'}),
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

class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['prescripcion', 'notas_adicionales']
        widgets = {
            'prescripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escriba los medicamentos y dosis aquí...'}),
            'notas_adicionales': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Indicaciones extra...'}),
        }