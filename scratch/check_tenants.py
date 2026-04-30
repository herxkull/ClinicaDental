import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica

for c in Clinica.objects.all():
    print(f"Clinica: {c.nombre_clinica} | Schema: {c.schema_name}")
