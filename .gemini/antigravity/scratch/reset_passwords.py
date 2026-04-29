import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from clientes.models import Clinica
from django_tenants.utils import schema_context

def reset_all_passwords():
    new_password = "admin123"
    print(f"--- RESETEANDO CONTRASEÑAS A '{new_password}' ---")
    
    clinicas = Clinica.objects.all() # Incluimos public por si acaso
    
    for c in clinicas:
        print(f"\nProcesando Esquema: {c.schema_name}...")
        with schema_context(c.schema_name):
            usuarios = User.objects.all()
            for u in usuarios:
                u.set_password(new_password)
                u.save()
                print(f"  - Contraseña actualizada para: {u.username}")

if __name__ == "__main__":
    reset_all_passwords()
