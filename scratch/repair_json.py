import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django_tenants.utils import schema_context
from gestion.models import GoogleCalendarConfig

def repair():
    schema = 'kimet'
    with schema_context(schema):
        config = GoogleCalendarConfig.objects.filter(is_active=True).first()
        if config and config.credentials_json:
            # Aseguramos que los campos obligatorios esten presentes
            data = config.credentials_json
            data['client_id'] = settings.GOOGLE_CLIENT_ID
            data['client_secret'] = settings.GOOGLE_CLIENT_SECRET
            data['token_uri'] = "https://oauth2.googleapis.com/token"
            
            config.credentials_json = data
            config.save()
            print("EXITO: JSON de credenciales reparado y actualizado.")
        else:
            print("No se encontro configuracion para reparar.")

if __name__ == "__main__":
    repair()
