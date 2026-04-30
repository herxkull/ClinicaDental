import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())
django.setup()

from clientes.models import Dominio

print("--- Listado de Dominios Registrados ---")
for d in Dominio.objects.all():
    print(f"ID: {d.id} | Dominio: {d.domain} | Tenant: {d.tenant.schema_name}")
