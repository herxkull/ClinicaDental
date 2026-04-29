import os
import sys
import django

# Añadir el directorio raíz al path para que encuentre 'config' y las apps
sys.path.append(os.getcwd())

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from django_tenants.utils import schema_context
from django.contrib.auth.models import User
from clientes.models import Clinica, Dominio

def test_onboarding():
    nombre = "Clínica Dental de Prueba"
    subdominio = "testclinic"
    email = "test@doctor.com"
    password = "password123"
    
    print(f"--- Iniciando creación de Tenant: {subdominio} ---")
    
    # 1. Limpiar si existe (para que el test sea repetible)
    # Primero borramos el dominio, luego la clínica
    try:
        Dominio.objects.filter(tenant__schema_name=subdominio).delete()
        Clinica.objects.filter(schema_name=subdominio).delete()
    except:
        pass
    
    try:
        with transaction.atomic():
            nueva_clinica = Clinica.objects.create(
                schema_name=subdominio,
                nombre_clinica=nombre
            )
            
            Dominio.objects.create(
                domain=f"{subdominio}.localhost",
                tenant=nueva_clinica,
                is_primary=True
            )
            print(f"OK: Tenant y Dominio creados para {subdominio}")

        # 2. Crear Superuser
        with schema_context(nueva_clinica.schema_name):
            if not User.objects.filter(username=email).exists():
                User.objects.create_superuser(
                    username=email,
                    email=email,
                    password=password
                )
                print(f"OK: Superuser '{email}' creado en el esquema '{subdominio}'")
            else:
                print(f"INFO: El usuario '{email}' ya existe en el esquema.")

        print("--- TEST EXITOSO ---")
        
    except Exception as e:
        print(f"ERROR: No se pudo completar el onboarding: {str(e)}")

if __name__ == "__main__":
    test_onboarding()
