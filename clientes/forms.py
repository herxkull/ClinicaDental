from django import forms
from .models import Clinica, Dominio

class RegistroClinicaForm(forms.Form):
    nombre_clinica = forms.CharField(
        max_length=100, 
        label="Nombre de la Clínica",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Clínica Dental Sonrisas'})
    )
    subdominio = forms.CharField(
        max_length=50, 
        label="Subdominio deseado",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo'})
    )
    email_admin = forms.EmailField(
        label="Correo electrónico del Administrador",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'doctor@ejemplo.com'})
    )
    password_admin = forms.CharField(
        label="Contraseña inicial",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Esta será la contraseña para el acceso inicial."
    )

    def clean_subdominio(self):
        subdominio = self.cleaned_data['subdominio'].lower().strip()
        # Verificar si ya existe el subdominio
        if Dominio.objects.filter(domain__iexact=f"{subdominio}.localhost").exists(): # Ajustar según dominio real
             raise forms.ValidationError("Este subdominio ya está en uso.")
        
        # Opcional: Validar caracteres permitidos (solo letras y números)
        if not subdominio.isalnum():
            raise forms.ValidationError("El subdominio solo puede contener letras y números.")
            
        return subdominio
