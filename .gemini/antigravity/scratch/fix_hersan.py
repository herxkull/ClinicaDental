import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Dominio, Clinica

def fix_hersan():
    print("--- ARREGLANDO CLÍNICA HERSAN ---")
    try:
        clinica = Clinica.objects.get(schema_name='hersandental')
        # Limpiar dominios viejos
        Dominio.objects.filter(tenant=clinica).delete()
        
        # Registrar ambas versiones
        Dominio.objects.create(domain='hersan.localhost:8000', tenant=clinica, is_primary=False)
        Dominio.objects.create(domain='hersan.localhost', tenant=clinica, is_primary=True)
        
        print("OK: Dominios para 'hersandental' actualizados correctamente.")
    except Clinica.DoesNotExist:
        print("ERROR: No se encontró la clínica con esquema 'hersandental'")

if __name__ == "__main__":
    fix_hersan()
