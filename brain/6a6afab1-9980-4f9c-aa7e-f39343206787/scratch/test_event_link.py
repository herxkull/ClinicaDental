import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from gestion.models import GoogleCalendarConfig
from gestion.google_calendar import get_calendar_service
from datetime import datetime, timedelta

with schema_context('pelusmi'):
    config = GoogleCalendarConfig.objects.filter(is_active=True).first()
    if config:
        service = get_calendar_service(config)
        if service:
            now = datetime.now()
            event_data = {
                'summary': "Prueba de Conexion DentalSaaS",
                'description': "Probando sincronizacion bidireccional desde Django.",
                'start': {
                    'dateTime': now.strftime('%Y-%m-%dT%H:%M:%S'),
                    'timeZone': 'America/Managua',
                },
                'end': {
                    'dateTime': (now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
                    'timeZone': 'America/Managua',
                },
            }
            try:
                event = service.events().insert(calendarId='primary', body=event_data).execute()
                print("Exito!")
                print("ID del Evento:", event['id'])
                print("Enlace del evento:", event.get('htmlLink'))
            except Exception as e:
                print("Error al crear evento:", e)
        else:
            print("No se pudo conectar al servicio de Google Calendar.")
    else:
        print("No se encontro configuracion activa de Google Calendar.")
