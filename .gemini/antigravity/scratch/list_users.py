import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from clientes.models import Clinica
from django_tenants.utils import schema_context

def list_tenant_users():
    print("--- USUARIOS REGISTRADOS POR CLÍNICA ---")
    clinicas = Clinica.objects.exclude(schema_name='public')
    
    for c in clinicas:
        print(f"\n[Clínica: {c.nombre_clinica} | Esquema: {c.schema_name}]")
        with schema_context(c.schema_name):
            usuarios = User.objects.filter(is_superuser=True)
            if not usuarios:
                print("  (!) No hay superusuarios en esta clínica.")
            for u in usuarios:
                print(f"  - Usuario/Email: {u.username}")
                print(f"    (La contraseña está encriptada)")

if __name__ == "__main__":
    list_tenant_users()
