import os
import sys
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())
django.setup()

from clientes.models import Clinica, Suscripcion

def backfill():
    print("--- Creando suscripciones iniciales para clínicas existentes ---")
    clinicas = Clinica.objects.exclude(schema_name='public')
    for c in clinicas:
        if not Suscripcion.objects.filter(clinica=c).exists():
            Suscripcion.objects.create(
                clinica=c,
                plan_tipo='BASICO',
                estado_pago='TRIAL',
                metodo_pago='TRANSFERENCIA',
                fecha_vencimiento=c.trial_end_date or (timezone.now() + timezone.timedelta(days=7))
            )
            print(f"[OK] Suscripción TRIAL creada para: {c.nombre_clinica}")
        else:
            print(f"[SKIP] {c.nombre_clinica} ya tiene una suscripción.")

if __name__ == "__main__":
    backfill()
