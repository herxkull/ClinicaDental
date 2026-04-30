import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from django.contrib.auth.models import User
from django.core.signing import TimestampSigner

def generate():
    schema = 'kimet'
    username = 'admin'
    signer = TimestampSigner()
    
    with schema_context(schema):
        u = User.objects.get(username=username)
        # Creamos un token que expire en 10 minutos
        token = signer.sign(u.username)
        
        print(f"--- TOKEN DE ACCESO DIRECTO GENERADO ---")
        print(f"Copia y pega esto en tu navegador:")
        print(f"http://{schema}.localhost:8000/magic-login/?token={token}")

if __name__ == "__main__":
    generate()
