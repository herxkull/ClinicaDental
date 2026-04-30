import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from django.contrib.auth import authenticate

def test():
    schema = 'kimet'
    user = 'admin'
    password = 'admin123'
    
    with schema_context(schema):
        user_obj = authenticate(username=user, password=password)
        if user_obj:
            print(f"✅ EXITO: El sistema acepta las credenciales de '{user}' en el esquema '{schema}'")
        else:
            print(f"❌ FALLO: El sistema RECHAZA las credenciales de '{user}'")

if __name__ == "__main__":
    test()
