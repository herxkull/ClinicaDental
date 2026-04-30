import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())
django.setup()

def check():
    from django_tenants.utils import schema_context
    from django.contrib.auth.models import User

    print("--- Verificando usuarios en esquema 'roec' ---")
    with schema_context('roec'):
        users = User.objects.all()
        if not users:
            print("No se encontraron usuarios en 'roec'.")
        for u in users:
            print(f"Usuario: {u.username} | Email: {u.email} | Superuser: {u.is_superuser}")

if __name__ == "__main__":
    check()
