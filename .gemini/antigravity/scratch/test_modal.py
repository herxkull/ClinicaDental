import os
import sys
import django
from django.test import RequestFactory
from django.urls import reverse

# Agregar el directorio actual al path
sys.path.append('C:\\Users\\her_s\\PycharmProjects\\ClinicaDental')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClinicaDental.settings')
django.setup()

from gestion.views import modal_nueva_cita
from gestion.models import Paciente
from django.contrib.auth.models import User

factory = RequestFactory()
paciente = Paciente.objects.first()

if paciente:
    url = reverse('modal_nueva_cita', kwargs={'paciente_id': paciente.id})
    request = factory.get(url)
    user = User.objects.first()
    request.user = user
    
    # Simular tenant si es necesario (django-tenants)
    from django.db import connection
    # Forzar esquema de hersan para el test
    connection.set_schema('hersan')
    
    try:
        response = modal_nueva_cita(request, paciente.id)
        print("Status Code:", response.status_code)
        if response.status_code != 200:
            print("Response Content:", response.content.decode()[:500])
    except Exception as e:
        print("Error during view execution:")
        import traceback
        traceback.print_exc()
else:
    print("No patient found to test.")
