import os
import sys
import django

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from django.utils import timezone
from datetime import time

# Configurar entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gestion.models import Paciente, Cita, Tratamiento, DoctorColaborador, Pago
from django_tenants.utils import schema_context

# Usar el esquema del tenant 'hersandental'
with schema_context('hersandental'):
    # 1. Crear Doctor Colaborador
    dr, created = DoctorColaborador.objects.get_or_create(
        nombre="Julián Estrada",
        defaults={
            "especialidad": "Endodoncia",
            "telefono": "555-0192",
            "email": "julian.estrada@prismo.com",
            "color_agenda": "#e67e22" # Naranja
        }
    )
    if created:
        print(f"Doctor {dr.nombre} creado.")
    else:
        print(f"Doctor {dr.nombre} ya existía.")

    # 2. Crear Tratamientos específicos para el doctor
    t1, _ = Tratamiento.objects.get_or_create(
        nombre="Endodoncia Molar",
        defaults={
            "precio_venta": 450.00,
            "comision_clinica_porcentaje": 40.00, # La clínica se queda con el 40%
            "doctor_referencia": dr,
            "color": "#e67e22"
        }
    )
    
    t2, _ = Tratamiento.objects.get_or_create(
        nombre="Cirugía Apical",
        defaults={
            "precio_venta": 600.00,
            "comision_clinica_porcentaje": 35.00,
            "doctor_referencia": dr,
            "color": "#d35400"
        }
    )
    print("Tratamientos especializados creados/actualizados.")

    # 3. Crear Citas de prueba
    paciente = Paciente.objects.first()
    if paciente:
        hoy = timezone.now().date()
        
        # Cita 1: Mañana
        c1 = Cita.objects.create(
            paciente=paciente,
            doctor=dr,
            tratamiento=t1,
            fecha=hoy + timezone.timedelta(days=1),
            hora=time(10, 0),
            motivo="Dolor persistente en molar superior",
            estado='CONFIRMADA'
        )
        
        # Cita 2: Próxima semana
        c2 = Cita.objects.create(
            paciente=paciente,
            doctor=dr,
            tratamiento=t2,
            fecha=hoy + timezone.timedelta(days=7),
            hora=time(15, 30),
            motivo="Seguimiento de cirugía programada",
            estado='PENDIENTE'
        )
        print(f"Citas creadas para {paciente.nombre} con el Dr. {dr.nombre}.")
    else:
        print("No se encontró ningún paciente en la base de datos para crear citas.")
