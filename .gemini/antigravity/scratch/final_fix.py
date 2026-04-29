import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Dominio, Clinica

def final_fix():
    print("--- SOLUCIÓN DEFINITIVA DE DOMINIOS ---")
    
    # 1. Asegurar que hdent tenga AMBOS dominios (con y sin puerto)
    try:
        clinica_hdent = Clinica.objects.get(schema_name='hdent')
        # Limpiar
        Dominio.objects.filter(tenant=clinica_hdent).delete()
        
        # Versión 1: Con puerto
        Dominio.objects.create(domain='hdent.localhost:8000', tenant=clinica_hdent, is_primary=False)
        # Versión 2: Sin puerto (por si el middleware lo limpia)
        Dominio.objects.create(domain='hdent.localhost', tenant=clinica_hdent, is_primary=True)
        
        print("OK: Creados 'hdent.localhost' y 'hdent.localhost:8000'")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Hacer lo mismo para el público
    try:
        public_tenant = Clinica.objects.get(schema_name='public')
        Dominio.objects.filter(tenant=public_tenant).delete()
        Dominio.objects.create(domain='localhost:8000', tenant=public_tenant, is_primary=False)
        Dominio.objects.create(domain='localhost', tenant=public_tenant, is_primary=True)
        print("OK: Dominios públicos normalizados.")
    except Exception as e:
        print(f"Error Public: {e}")

if __name__ == "__main__":
    final_fix()
