import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from django.contrib.auth.models import User

def create():
    schema = 'kimet'
    with schema_context(schema):
        # Crear o actualizar usuario 'admin'
        u, created = User.objects.get_or_create(username='admin')
        u.set_password('admin123')
        u.email = 'admin@kimet.com'
        u.is_active = True
        u.is_staff = True
        u.is_superuser = True
        u.save()
        print(f"Usuario 'admin' {'CREADO' if created else 'ACTUALIZADO'} en esquema '{schema}'")

if __name__ == "__main__":
    create()
