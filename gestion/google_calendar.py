import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from .models import GoogleCalendarConfig, Cita

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def get_calendar_service(config):
    """Obtiene el servicio de Google Calendar usando las credenciales del modelo"""
    if not config or not config.credentials_json:
        print("DEBUG: GoogleCalendarConfig o credentials_json están vacíos.")
        return None
    
    saved_scopes = config.credentials_json.get('scopes', SCOPES)
    creds = Credentials.from_authorized_user_info(config.credentials_json, saved_scopes)
    
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            import json
            config.credentials_json = json.loads(creds.to_json())
            config.save()
        except Exception as e:
            print(f"Error refreshing credentials: {e}")
        
    return build('calendar', 'v3', credentials=creds)


def sync_cita_to_google(cita):
    """Sincroniza una cita individual con Google Calendar"""
    config = GoogleCalendarConfig.objects.filter(is_active=True).first()
    if not config:
        raise Exception("No hay una configuración activa de Google Calendar.")
        
    service = get_calendar_service(config)
    
    if not service:
        raise Exception("No se pudo establecer conexión con el servicio de Google Calendar. Verifica tus credenciales.")

    prefix = "✅ [FINALIZADA] " if cita.estado == 'COMPLETADA' else "🦷 Cita: "
    # Asegurar que fecha y hora son objetos date/time
    from datetime import datetime, date, time, timedelta
    
    fecha_obj = cita.fecha
    if isinstance(fecha_obj, str):
        fecha_obj = date.fromisoformat(fecha_obj)
        
    hora_obj = cita.hora
    if isinstance(hora_obj, str):
        # Manejar formatos HH:MM o HH:MM:SS
        hora_obj = time.fromisoformat(hora_obj)

    # Calculamos inicio y fin (1 hora después)
    start_dt_obj = datetime.combine(fecha_obj, hora_obj)
    end_dt_obj = start_dt_obj + timedelta(hours=1)

    event_data = {
        'summary': f"{prefix}{cita.paciente.nombre}",
        'description': f"Tratamiento: {cita.tratamiento.nombre if cita.tratamiento else 'Consulta'}\nMotivo: {cita.motivo}",
        'start': {
            'dateTime': start_dt_obj.strftime('%Y-%m-%dT%H:%M:%S'),
            'timeZone': 'America/Managua',
        },
        'end': {
            'dateTime': end_dt_obj.strftime('%Y-%m-%dT%H:%M:%S'),
            'timeZone': 'America/Managua',
        },
    }

    try:
        calendar_id = config.calendar_id if config.calendar_id else 'primary'
        
        if cita.google_event_id:
            # Actualizar existente
            event = service.events().update(
                calendarId=calendar_id, 
                eventId=cita.google_event_id, 
                body=event_data
            ).execute()
        else:
            # Crear nuevo
            event = service.events().insert(
                calendarId=calendar_id, 
                body=event_data
            ).execute()
            cita.google_event_id = event['id']
            cita.save()
        return event['id']
    except Exception as e:
        error_msg = f"Error sincronizando con Google: {str(e)}"
        print(error_msg)
        raise Exception(error_msg) # Re-lanzamos para que la vista lo capture

def delete_google_event(cita):
    """Elimina el evento de Google si la cita se borra en Django"""
    if not cita.google_event_id:
        return
    
    config = GoogleCalendarConfig.objects.filter(is_active=True).first()
    service = get_calendar_service(config)
    if service:
        try:
            service.events().delete(calendarId=config.calendar_id, eventId=cita.google_event_id).execute()
        except:
            pass
def fetch_google_events(config, start_date=None, end_date=None):
    """Trae eventos de Google Calendar para mostrarlos en el calendario de Django"""
    service = get_calendar_service(config)
    if not service:
        return []
    
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Por defecto, traer desde hoy hasta 30 días después
        time_min = (start_date or timezone.now()).isoformat()
        if not time_min.endswith('Z'): time_min += 'Z'
        
        events_result = service.events().list(
            calendarId=config.calendar_id, 
            timeMin=time_min,
            maxResults=50, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except Exception as e:
        print(f"Error recuperando eventos de Google: {e}")
        return []
