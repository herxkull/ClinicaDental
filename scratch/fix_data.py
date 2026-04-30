import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica, Suscripcion

print("\n--- REPARACIÓN MASIVA DE SUSCRIPCIONES ---")
vencimiento_default = timezone.now() + timedelta(days=30)

for suscripcion in Suscripcion.objects.filter(estado_pago__in=['APROBADO', 'CORTESIA']):
    if not suscripcion.fecha_vencimiento:
        print(f"Reparando suscripcion de: {suscripcion.clinica.nombre_clinica}")
        suscripcion.fecha_vencimiento = vencimiento_default
        suscripcion.save()
        
        # Sincronizar clínica
        clinica = suscripcion.clinica
        clinica.is_trial = False
        clinica.trial_end_date = vencimiento_default
        clinica.save()
        print(f"  -> Clínica {clinica.nombre_clinica} sincronizada y Trial desactivado.")

print("\n--- REPARACIÓN COMPLETADA ---")
