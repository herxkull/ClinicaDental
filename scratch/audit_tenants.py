import os
import sys
import django
from django.utils import timezone

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica, Suscripcion

print("\n--- AUDITORÍA DE CLÍNICAS Y SUSCRIPCIONES ---")
for clinica in Clinica.objects.all():
    print(f"\nClinica: {clinica.nombre_clinica} (Schema: {clinica.schema_name})")
    print(f"  - Activa: {clinica.is_active}")
    print(f"  - Modo Trial: {clinica.is_trial}")
    print(f"  - Trial End: {clinica.trial_end_date}")
    print(f"  - Suscripcion Activa (Propiedad): {clinica.suscripcion_activa}")
    
    print("  - Historial de Suscripciones:")
    for s in clinica.suscripciones.all():
        print(f"    * Plan: {s.plan_tipo} | Estado: {s.estado_pago} | Vence: {s.fecha_vencimiento}")
print("\n--- FIN DE AUDITORÍA ---")
