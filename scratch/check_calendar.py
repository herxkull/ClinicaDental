import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from gestion.models import GoogleCalendarConfig

def check():
    schema = 'kimet'
    with schema_context(schema):
        print(f"--- REVISANDO GOOGLE CALENDAR EN: {schema} ---")
        config = GoogleCalendarConfig.objects.filter(is_active=True).first()
        if config:
            print(f"Configuracion encontrada: SI")
            print(f"ID Calendario: {config.calendar_id}")
            print(f"Tiene credenciales JSON: {'SI' if config.credentials_json else 'NO'}")
            if config.credentials_json:
                keys = config.credentials_json.keys()
                print(f"Campos en JSON: {list(keys)}")
                print(f"Tiene Refresh Token: {'refresh_token' in config.credentials_json}")
        else:
            print("Configuracion encontrada: NO")

if __name__ == "__main__":
    check()
