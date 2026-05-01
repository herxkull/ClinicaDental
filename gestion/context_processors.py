from .models import ConfiguracionClinica

def clinica_config(request):
    """Hace que la configuración de la clínica esté disponible en todos los templates de forma segura"""
    try:
        # 1. Si no hay tenant o es el esquema público, no buscar configuración
        tenant = getattr(request, 'tenant', None)
        if not tenant or tenant.schema_name == 'public':
            return {'clinica_config': None}
        
        # 2. Si el usuario no está autenticado, opcionalmente podrías devolver None 
        # (pero a veces queremos ver la marca en la pantalla de login del tenant)
        # Por ahora lo dejamos pasar si hay tenant.

        config = ConfiguracionClinica.objects.first()
        return {
            'clinica_config': config
        }
    except Exception as e:
        # 3. Fallback total para evitar Error 500 en producción
        print(f"Error en clinica_config context processor: {e}")
        return {
            'clinica_config': None
        }
