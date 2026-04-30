import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())
django.setup()

from clientes.models import Suscripcion

def fix_methods():
    print("--- Actualizando métodos de pago para cuentas Trial ---")
    updated = Suscripcion.objects.filter(estado_pago='TRIAL').update(metodo_pago='GRATIS')
    print(f"¡Éxito! Se han actualizado {updated} registros a método 'GRATIS'.")

if __name__ == "__main__":
    fix_methods()
