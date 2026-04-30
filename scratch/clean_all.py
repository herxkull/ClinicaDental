import os
import sys
import django

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica

print("\n--- LIMPIEZA TOTAL DE DENSAAS ---")
clinicas = Clinica.objects.all()
count = clinicas.count()

if count == 0:
    print("No hay clínicas para eliminar.")
else:
    print(f"Eliminando {count} clínicas y sus esquemas...")
    for clinica in clinicas:
        nombre = clinica.nombre_clinica
        schema = clinica.schema_name
        try:
            # Al eliminar el objeto Clinica (Tenant), django-tenants se encarga de borrar el esquema
            clinica.delete()
            print(f"  [OK] Eliminada: {nombre} (Esquema: {schema})")
        except Exception as e:
            print(f"  [ERROR] No se pudo eliminar {nombre}: {e}")

print("\n--- LIMPIEZA COMPLETADA. LISTO PARA PRUEBAS DESDE CERO ---")
