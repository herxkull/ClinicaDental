import os
import sys
import django

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Suscripcion

# Eliminar la suscripción más antigua (la de Trial)
sub_trial = Suscripcion.objects.filter(estado_pago='TRIAL').first()
if sub_trial:
    print(f"Eliminando suscripción duplicada ID: {sub_trial.pk}")
    sub_trial.delete()
    print("Suscripción eliminada con éxito.")
else:
    print("No se encontró ninguna suscripción en estado TRIAL para eliminar.")
