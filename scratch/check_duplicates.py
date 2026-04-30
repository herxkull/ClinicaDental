import os
import sys
import django

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica

print("\n--- REVISIÓN DE CLÍNICAS REGISTRADAS ---")
clinicas = Clinica.objects.all()

if not clinicas.exists():
    print("No hay ninguna clínica registrada.")
else:
    for c in clinicas:
        print(f"ID: {c.pk} | Nombre: {c.nombre_clinica} | Schema: {c.schema_name} | Creada: {c.trial_start_date}")

print("\n--- FIN DE LA REVISIÓN ---")
