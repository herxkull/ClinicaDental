import os
import sys
import django

# Asegurarnos de que el directorio raíz esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Usar el pooler de sesión (puerto 5432) y usuario del proyecto de Supabase
os.environ['DB_NAME'] = 'postgres'
os.environ['DB_USER'] = 'postgres.yorshrwsrqgdjwvsfdkq'
os.environ['DB_PASSWORD'] = 'Tenesketchu15/-'
os.environ['DB_HOST'] = 'aws-1-us-east-1.pooler.supabase.com'
os.environ['DB_PORT'] = '5432'

django.setup()

from django.contrib.auth.models import User
from django_tenants.utils import schema_context

print("Conectando a la base de datos de Supabase...")
with schema_context('public'):
    username = 'admin'
    email = 'admin@ejemplo.com'
    password = 'adminpassword123'
    
    user, created = User.objects.get_or_create(username=username)
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    
    if created:
        print(f"¡Usuario '{username}' creado exitosamente en el esquema público!")
    else:
        print(f"La contraseña del usuario '{username}' ha sido actualizada y reestablecida.")
