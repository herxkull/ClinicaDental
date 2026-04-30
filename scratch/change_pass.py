import os
import sys
import django

# Añadir el directorio actual al path
sys.path.append(os.getcwd())

# Configuración de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from django.contrib.auth.models import User

def change():
    try:
        with schema_context('kimet'):
            u = User.objects.get(email='hersanhs15@gmail.com')
            u.set_password('admin123')
            u.save()
            print("✅ Contraseña de 'kimet' actualizada a: admin123")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    change()
