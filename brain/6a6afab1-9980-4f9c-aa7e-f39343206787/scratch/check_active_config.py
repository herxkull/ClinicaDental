import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from gestion.models import GoogleCalendarConfig, Cita

with schema_context('pelusmi'):
    config = GoogleCalendarConfig.objects.filter(is_active=True).first()
    if config:
        print(f"Configuración activa encontrada!")
        print(f"ID del Calendario: {config.calendar_id}")
        print(f"Campos en credentials_json: {list(config.credentials_json.keys())}")
        
        # Veamos si la última cita creada tiene un google_event_id guardado
        ultima_cita = Cita.objects.order_by('-id').first()
        if ultima_cita:
            print(f"Última cita ID: {ultima_cita.id}")
            print(f"Google Event ID: {ultima_cita.google_event_id}")
    else:
        print("No se encontró ninguna configuración activa de Google Calendar.")
