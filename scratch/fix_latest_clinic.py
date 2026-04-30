import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())
django.setup()

from clientes.models import Clinica, Dominio

def fix_latest():
    # Obtener la última clínica creada (excluyendo public)
    latest = Clinica.objects.exclude(schema_name='public').order_by('-id').first()
    if not latest:
        print("No se encontraron clínicas.")
        return

    print(f"--- Reparando última clínica: {latest.schema_name} ---")
    sub = latest.schema_name
    
    # Variantes con puerto (asumiendo 8000)
    puerto = ":8000"
    variantes = [
        f"{sub}.localhost{puerto}",
        f"{sub}.127.0.0.1{puerto}",
        f"{sub}.127.0.0.1.nip.io{puerto}",
        f"{sub}.localhost",
        f"{sub}.127.0.0.1"
    ]

    for d_name in variantes:
        obj, created = Dominio.objects.get_or_create(
            domain=d_name,
            tenant=latest
        )
        if created:
            print(f"[NUEVO] Dominio: {d_name}")
        else:
            print(f"[OK] Dominio ya existe: {d_name}")

if __name__ == "__main__":
    fix_latest()
