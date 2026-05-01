import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from clientes.models import Clinica, Suscripcion
from django.utils import timezone

c = Clinica.objects.get(schema_name='pelusmi')
print(f"--- Clinica {c.nombre_clinica} ---")
print(f"Plan: {c.plan}")
print(f"Is Trial: {c.is_trial}")
print(f"Trial Start Date: {c.trial_start_date}")
print(f"Trial End Date: {c.trial_end_date}")
print(f"Trial Expirado: {c.trial_expirado}")
print(f"Dias Restantes: {c.dias_restantes}")
print(f"Suscripcion Activa: {c.suscripcion_activa}")

print("\n--- Suscripciones de la clínica ---")
suscripciones = Suscripcion.objects.filter(clinica=c)
for s in suscripciones:
    print(f"Suscripcion ID: {s.id}")
    print(f"  Plan: {s.plan_tipo}")
    print(f"  Estado Pago: {s.estado_pago}")
    print(f"  Metodo Pago: {s.metodo_pago}")
    print(f"  Fecha Vencimiento: {s.fecha_vencimiento}")
