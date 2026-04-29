import os
import sys
import django

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django_tenants.utils import schema_context

def create_global_admin():
    username = "admin"
    email = "admin@clinica.com"
    password = "admin123"
    
    print(f"--- Creando Superusuario Global en esquema 'public' ---")
    
    # Nos aseguramos de estar en el esquema público
    with schema_context('public'):
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"OK: Superusuario '{username}' creado exitosamente.")
            print(f"User: {username}")
            print(f"Pass: {password}")
        else:
            # Si existe, le reseteamos la contraseña por si no la recuerda
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print(f"INFO: El usuario '{username}' ya existía. Se ha actualizado su contraseña a '{password}'.")

if __name__ == "__main__":
    create_global_admin()
