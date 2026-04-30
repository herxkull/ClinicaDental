
import os
import sys
import django

# Añadir el directorio raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import tenant_context
from clientes.models import Clinica
from gestion.models import GoogleCalendarConfig, Cita

def check_sync_status():
    print("Iniciando auditoría de sincronización...")
    
    # Buscar el tenant
    tenant = Clinica.objects.get(schema_name='hersandental')
    
    with tenant_context(tenant):
        config = GoogleCalendarConfig.objects.filter(id=1).first()
        if not config:
            print("Error: No se encontró configuración de Google Calendar (ID=1)")
            return
            
        print(f"Configuración encontrada:")
        print(f" - Activo: {config.is_active}")
        print(f" - Calendar ID: {config.calendar_id or 'primary'}")
        print(f" - Tiene credenciales: {'Sí' if config.credentials_json else 'No'}")
        
        # Revisar últimas citas
        ultimas_citas = Cita.objects.all().order_by('-id')[:5]
        print("\nÚltimas 5 citas:")
        for c in ultimas_citas:
            print(f" - ID: {c.id} | Paciente: {c.paciente.nombre} | Google Event ID: {c.google_event_id or 'NINGUNO'}")

if __name__ == "__main__":
    check_sync_status()
