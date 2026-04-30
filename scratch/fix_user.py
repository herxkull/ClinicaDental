import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from django.contrib.auth.models import User

def fix():
    schema = 'kimet'
    email_target = 'hersanhs15@gmail.com'
    
    with schema_context(schema):
        print(f"--- REVISANDO ESQUEMA: {schema} ---")
        try:
            # Buscamos por email o por username
            u = User.objects.filter(email=email_target).first()
            if not u:
                u = User.objects.filter(username=email_target).first()
            
            if u:
                u.set_password('admin123')
                u.is_active = True
                u.is_staff = True
                u.is_superuser = True
                u.save()
                print(f"EXITO: Usuario '{u.username}' actualizado.")
                print(f"Utiliza este username exacto para entrar: {u.username}")
            else:
                print("ERROR: No se encontro el usuario en este esquema.")
                # Listar todos por si acaso
                print("Usuarios disponibles:")
                for user in User.objects.all():
                    print(f"- {user.username}")
        except Exception as e:
            print(f"ERROR CRITICO: {e}")

if __name__ == "__main__":
    fix()
