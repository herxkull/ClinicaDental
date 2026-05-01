import os
import sys
import django

# Asegurarnos de que el directorio raíz esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuramos las variables de entorno para conectarnos a Supabase directamente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Configura tus credenciales de Supabase aquí antes de correr el script
os.environ['DB_NAME'] = 'postgres'
os.environ['DB_USER'] = 'postgres.yorshrwsrqgdjwvsfdkq'
os.environ['DB_PASSWORD'] = 'Tenesketchu15/-'
os.environ['DB_HOST'] = 'aws-1-us-east-1.pooler.supabase.com'
os.environ['DB_PORT'] = '6543'

django.setup()

from django.contrib.auth.models import User
from django_tenants.utils import schema_context

# Crear el superusuario en el esquema público
with schema_context('public'):
    username = 'admin'
    email = 'admin@ejemplo.com'
    password = 'adminpassword123'  # REEMPLAZA CON LA CONTRASEÑA QUE QUIERAS
    
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"¡Superusuario '{username}' creado exitosamente en el esquema público!")
    else:
        print(f"El usuario '{username}' ya existe.")
