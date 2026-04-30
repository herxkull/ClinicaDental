import os
import sys
import django

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica, Dominio

def fix():
    print("Iniciando reparación de Esquema Público...")
    # 1. Crear o recuperar la clínica pública
    public_tenant, created = Clinica.objects.get_or_create(
        schema_name='public',
        defaults={'nombre_clinica': 'Admin SaaS'}
    )
    if created:
        print("Esquema 'public' creado con éxito.")
    else:
        print("Esquema 'public' ya existía.")

    # 2. Asegurar el dominio localhost para el público
    dom, dom_created = Dominio.objects.get_or_create(
        domain='localhost',
        tenant=public_tenant,
        defaults={'is_primary': True}
    )
    
    # También añadimos 127.0.0.1 por si acaso
    Dominio.objects.get_or_create(
        domain='127.0.0.1',
        tenant=public_tenant,
        defaults={'is_primary': False}
    )

    if dom_created:
        print("Dominio 'localhost' asociado al esquema público.")
    else:
        print("Dominio 'localhost' ya estaba asociado.")

    print("--- REPARACIÓN COMPLETADA ---")

if __name__ == "__main__":
    fix()
