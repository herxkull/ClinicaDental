import os
import sys
import django

# Añadir el directorio actual al path
sys.path.append(os.getcwd())

# Configuración de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from clientes.models import Clinica, Dominio
from django.contrib.auth.models import User

def inspect():
    print("=== INSPECCIÓN DE CLÍNICAS (Esquema Público) ===")
    clinicas = Clinica.objects.all()
    for c in clinicas:
        print(f"ID: {c.id} | Schema: {c.schema_name} | Email Contacto: {c.email_contacto}")
        
        # Ver usuarios dentro de cada clínica
        if c.schema_name != 'public':
            try:
                with schema_context(c.schema_name):
                    usuarios = User.objects.all()
                    print(f"  -> Usuarios en {c.schema_name}:")
                    if not usuarios:
                        print("     - [SIN USUARIOS]")
                    for u in usuarios:
                        print(f"     - {u.username} (Email: {u.email})")
            except Exception as e:
                print(f"  -> Error al leer esquema {c.schema_name}: {e}")

if __name__ == "__main__":
    inspect()
