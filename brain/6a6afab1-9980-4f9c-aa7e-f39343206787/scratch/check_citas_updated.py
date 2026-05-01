import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from clientes.models import Clinica
from gestion.models import Cita

tenants = Clinica.objects.exclude(schema_name='public')
for t in tenants:
    with schema_context(t.schema_name):
        citas = Cita.objects.filter(doctor__isnull=True)
        print(f"Tenant {t.schema_name}: Quedan {citas.count()} citas sin doctor.")
