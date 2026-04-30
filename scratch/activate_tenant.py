import os
import sys
import django

# Configuración de entorno
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica, Dominio

def activate(schema_name):
    try:
        tenant = Clinica.objects.get(schema_name=schema_name)
        print(f"Clínica encontrada: {tenant.nombre_clinica} (Esquema: {schema_name})")
        
        # Variantes de dominio para asegurar detección
        dominios = [
            f"{schema_name}.localhost",
            f"{schema_name}.localhost:8000",
            f"{schema_name}.127.0.0.1",
            f"{schema_name}.127.0.0.1:8000",
        ]
        
        for i, dom_name in enumerate(dominios):
            dom, created = Dominio.objects.get_or_create(
                domain=dom_name,
                tenant=tenant,
                defaults={'is_primary': (i == 0)}
            )
            if created:
                print(f" [+] Dominio registrado: {dom_name}")
            else:
                print(f" [!] Dominio ya existía: {dom_name}")
                
        print("\n--- PROCESO COMPLETADO ---")
        print(f"Ahora deberías poder entrar en: http://{schema_name}.localhost:8000/")
        
    except Clinica.DoesNotExist:
        print(f"Error: No existe ninguna clínica con el esquema '{schema_name}'")

if __name__ == "__main__":
    activate('kimet')
