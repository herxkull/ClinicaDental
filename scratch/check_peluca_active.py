import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())
django.setup()

from clientes.models import Clinica

try:
    tenant = Clinica.objects.get(schema_name='peluca')
    print(f"--- Estado de '{tenant.schema_name}' ---")
    print(f"Nombre: {tenant.nombre_clinica}")
    print(f"Activo: {tenant.is_active}")
    print(f"Trial: {tenant.is_trial}")
    print(f"Plan: {tenant.plan}")
    
    if not tenant.is_active:
        print("\n[!] ADVERTENCIA: La clínica está INACTIVA. Activándola...")
        tenant.is_active = True
        tenant.save()
        print("[OK] Clínica activada.")
except Clinica.DoesNotExist:
    print("El tenant 'peluca' no existe.")
