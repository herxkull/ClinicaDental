import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from gestion.models import Cita
from gestion import google_calendar

def sync():
    schema = 'kimet'
    with schema_context(schema):
        print(f"--- INTENTANDO SINCRONIZACION MANUAL EN: {schema} ---")
        cita = Cita.objects.last()
        if cita:
            print(f"Sincronizando cita ID {cita.id} de {cita.paciente.nombre}...")
            try:
                event_id = google_calendar.sync_cita_to_google(cita)
                print(f"EXITO: Evento creado/actualizado con ID: {event_id}")
            except Exception as e:
                print(f"FALLO: {e}")
        else:
            print("No hay citas para sincronizar.")

if __name__ == "__main__":
    sync()
