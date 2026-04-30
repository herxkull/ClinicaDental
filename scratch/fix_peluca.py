import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())
django.setup()

from clientes.models import Clinica, Dominio

def fix_tenant(schema, subdominio):
    print(f"--- Diagnóstico para: {schema} ---")
    try:
        tenant = Clinica.objects.get(schema_name=schema)
        print(f"Tenant encontrado: {tenant.nombre_clinica}")
        
        # Versiones de dominio a asegurar
        expected_domains = [
            f"{subdominio}.localhost:8000",
            f"{subdominio}.localhost"
        ]
        
        for domain_name in expected_domains:
            obj, created = Dominio.objects.get_or_create(
                domain=domain_name,
                tenant=tenant,
                defaults={'is_primary': (domain_name == expected_domains[0])}
            )
            if created:
                print(f"[NUEVO] Dominio creado: {domain_name}")
            else:
                print(f"[OK] Dominio ya existe: {domain_name}")
                
        print("¡Reparación completada!")
    except Clinica.DoesNotExist:
        print(f"Error: El tenant '{schema}' no existe.")

if __name__ == "__main__":
    fix_tenant('peluca', 'peluca')
