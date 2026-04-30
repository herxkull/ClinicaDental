import os
import sys
import django
from google.oauth2.credentials import Credentials

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from gestion.models import GoogleCalendarConfig

def debug():
    schema = 'kimet'
    with schema_context(schema):
        config = GoogleCalendarConfig.objects.filter(is_active=True).first()
        if config and config.credentials_json:
            print(f"DEBUG JSON KEYS: {list(config.credentials_json.keys())}")
            # Intentamos emular lo que hace la libreria
            try:
                creds = Credentials.from_authorized_user_info(config.credentials_json)
                print("Libreria acepto el JSON")
                print(f"Refresh Token presente en objeto: {creds.refresh_token is not None}")
                print(f"Client ID presente en objeto: {creds.client_id is not None}")
            except Exception as e:
                print(f"Error en libreria: {e}")
        else:
            print("No hay JSON")

if __name__ == "__main__":
    debug()
