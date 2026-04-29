import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Dominio, Clinica

def deep_clean_domains():
    print("--- LIMPIEZA PROFUNDA DE DOMINIOS ---")
    
    # 1. Eliminar duplicados y limpiar espacios
    for d in Dominio.objects.all():
        clean_name = d.domain.strip().lower()
        if d.domain != clean_name:
            print(f"Reparando: '{d.domain}' -> '{clean_name}'")
            d.domain = clean_name
            d.save()

    # 2. Asegurar que hdent tenga el dominio correcto
    try:
        clinica_hdent = Clinica.objects.get(schema_name='hdent')
        # Borramos dominios viejos de hdent para re-crearlos limpios
        Dominio.objects.filter(tenant=clinica_hdent).delete()
        
        # Creamos la versión con puerto que es la que detectó el Ping
        Dominio.objects.create(
            domain='hdent.localhost:8000',
            tenant=clinica_hdent,
            is_primary=True
        )
        print("OK: Dominio 'hdent.localhost:8000' re-creado correctamente.")
    except Clinica.DoesNotExist:
        print("ERROR: No se encontró la clínica con esquema 'hdent'")

if __name__ == "__main__":
    deep_clean_domains()
