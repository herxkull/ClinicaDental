
import os
import sys
import django

# Añadir el directorio raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica, Dominio

def make_localhost_primary():
    print("Reconfigurando localhost para la clínica...")
    
    # 1. Quitar 'localhost' del tenant public (Admin SaaS)
    public_tenant = Clinica.objects.get(schema_name='public')
    Dominio.objects.filter(domain='localhost').delete()
    
    # Asegurar que el public tenga otro dominio para no quedar huérfano
    Dominio.objects.get_or_create(tenant=public_tenant, domain='admin.localhost')
    print("Admin SaaS movido a http://admin.localhost:8000")

    # 2. Asignar 'localhost' a Hersan Dental
    clinica = Clinica.objects.filter(schema_name='hersandental').first()
    if clinica:
        Dominio.objects.get_or_create(tenant=clinica, domain='localhost')
        print(f"Clínica {clinica.nombre_clinica} ahora responde en http://localhost:8000")
    
    print("¡Listo! Ahora puedes usar localhost para Google OAuth.")

if __name__ == "__main__":
    make_localhost_primary()
