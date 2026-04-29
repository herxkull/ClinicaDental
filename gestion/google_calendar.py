import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from .models import GoogleCalendarConfig, Cita

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service(config):
    """Obtiene el servicio de Google Calendar usando las credenciales del modelo"""
    if not config or not config.credentials_json:
        return None
    
    creds = Credentials.from_authorized_user_info(config.credentials_json, SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        config.credentials_json = creds.to_json()
        config.save()
        
    return build('calendar', 'v3', credentials=creds)

def sync_cita_to_google(cita):
    """Sincroniza una cita individual con Google Calendar"""
    config = GoogleCalendarConfig.objects.filter(is_active=True).first()
    service = get_calendar_service(config)
    
    if not service:
        return None

    prefix = "✅ [COMPLETADA] " if cita.completada else "🦷 Cita: "
    from datetime import datetime, timedelta

    # Calculamos fin (1 hora después)
    start_dt_obj = datetime.combine(cita.fecha, cita.hora)
    end_dt_obj = start_dt_obj + timedelta(hours=1)

    event_data = {
        'summary': f"{prefix}{cita.paciente.nombre}",
        'description': f"Tratamiento: {cita.tratamiento.nombre if cita.tratamiento else 'Consulta'}\nMotivo: {cita.motivo}",
        'start': {
            'dateTime': start_dt_obj.isoformat(),
            'timeZone': 'America/Managua',
        },
        'end': {
            'dateTime': end_dt_obj.isoformat(),
            'timeZone': 'America/Managua',
        },
    }

    try:
        if cita.google_event_id:
            # Actualizar existente
            event = service.events().update(
                calendarId=config.calendar_id, 
                eventId=cita.google_event_id, 
                body=event_data
            ).execute()
        else:
            # Crear nuevo
            event = service.events().insert(
                calendarId=config.calendar_id, 
                body=event_data
            ).execute()
            cita.google_event_id = event['id']
            cita.save()
        return event['id']
    except Exception as e:
        print(f"Error sincronizando con Google: {e}")
        return None

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
