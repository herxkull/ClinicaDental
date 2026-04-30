import os
import sys
import django

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Suscripcion

print("\n--- REVISIÓN DE SUSCRIPCIONES ---")
subs = Suscripcion.objects.all()

if not subs.exists():
    print("No hay ninguna suscripción registrada.")
else:
    for s in subs:
        print(f"ID: {s.pk} | Clínica: {s.clinica.nombre_clinica} | Plan: {s.plan_tipo} | Estado: {s.estado_pago} | Inicio: {s.fecha_inicio}")

print("\n--- FIN DE LA REVISIÓN ---")
