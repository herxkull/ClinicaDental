# clientes/views.py
from django.shortcuts import render, redirect
from django.db import transaction
from django_tenants.utils import schema_context
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.conf import settings
from .forms import RegistroClinicaForm
from .models import Clinica, Dominio
from gestion.models import Tratamiento # Importamos el modelo para crear datos base

def home_publico(request):
    return render(request, 'clientes/index.html')

def registro_clinica(request):
    if request.method == 'POST':
        form = RegistroClinicaForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre_clinica']
            subdominio = form.cleaned_data['subdominio']
            email = form.cleaned_data['email_admin']
            password = form.cleaned_data['password_admin']
            
            # 1. Crear el Tenant y el Dominio dentro de una transacción
            try:
                with transaction.atomic():
                    # El schema_name suele ser el subdominio o un slug
                    schema_name = subdominio
                    
                    nueva_clinica = Clinica.objects.create(
                        schema_name=schema_name,
                        nombre_clinica=nombre
                    )
                    
                    # Construir el dominio completo preservando el puerto en desarrollo
                    host_completo = request.get_host()
                    host_actual = host_completo.split(':')[0]
                    
                    if 'localhost' in host_actual or '127.0.0.1' in host_actual:
                        # Si hay puerto (ej. :8000), lo mantenemos
                        puerto = ":" + host_completo.split(':')[1] if ':' in host_completo else ""
                        domain_full = f"{subdominio}.localhost{puerto}"
                    else:
                        domain_full = f"{subdominio}.{host_actual}"

                    Dominio.objects.create(
                        domain=domain_full,
                        tenant=nueva_clinica,
                        is_primary=True
                    )
                    
                # 2. Crear el Superusuario dentro del nuevo esquema
                # django-tenants disparará la creación de tablas automáticamente tras el commit si auto_create_schema=True
                # pero necesitamos asegurarnos de que las tablas existan antes de crear el usuario.
                # Con auto_create_schema=True, django-tenants crea el esquema en el post_save.
                
                with schema_context(nueva_clinica.schema_name):
                    # Crear el usuario administrador de la clínica
                    user = User.objects.create_superuser(
                        username=email, # Usamos email como username para simplificar
                        email=email,
                        password=password
                    )
                    user.is_staff = True
                    user.save()

                    # 2.1. Crear datos de ejemplo (Tratamientos Base)
                    Tratamiento.objects.bulk_create([
                        Tratamiento(nombre="Consulta General", costo_base=20.00, descripcion="Evaluación inicial y diagnóstico."),
                        Tratamiento(nombre="Limpieza Dental", costo_base=35.00, descripcion="Profilaxis y eliminación de sarro."),
                        Tratamiento(nombre="Resina (Calza)", costo_base=45.00, descripcion="Restauración estética de pieza dental."),
                        Tratamiento(nombre="Extracción Simple", costo_base=30.00, descripcion="Remoción de pieza dental no compleja."),
                        Tratamiento(nombre="Radiografía", costo_base=15.00, descripcion="Toma de rayos X dental."),
                    ])

                # 3. Enviar correo de bienvenida
                try:
                    context_email = {
                        'nombre_doctor': nombre, # Podríamos pedir nombre del doctor aparte, de momento usamos el de la clínica
                        'nombre_clinica': nombre,
                        'url_acceso': f"http://{domain_full}",
                        'email': email
                    }
                    mensaje_texto = render_to_string('clientes/emails/bienvenida.txt', context_email)
                    mensaje_html = render_to_string('clientes/emails/bienvenida.html', context_email)
                    
                    send_mail(
                        subject=f'Bienvenido a DentalSaaS - {nombre}',
                        message=mensaje_texto,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                        html_message=mensaje_html
                    )
                except Exception as mail_error:
                    print(f"Error enviando correo: {mail_error}")
                    # No detenemos el proceso si el correo falla

                return render(request, 'clientes/registro_exitoso.html', {
                    'clinica': nueva_clinica,
                    'url_acceso': f"http://{domain_full}"
                })
                
            except Exception as e:
                form.add_error(None, f"Error al crear la clínica: {str(e)}")
    else:
        form = RegistroClinicaForm()
        
    return render(request, 'clientes/registro.html', {'form': form})