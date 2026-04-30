import os
import sys
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())
django.setup()

with connection.cursor() as cursor:
    cursor.execute("SELECT schema_name FROM information_schema.schemata;")
    schemas = [row[0] for row in cursor.fetchall()]
    print("--- Esquemas en la Base de Datos ---")
    for s in schemas:
        print(f"- {s}")

if 'peluca' in schemas:
    print("\n[OK] El esquema 'peluca' EXISTE.")
else:
    print("\n[ERROR] El esquema 'peluca' NO EXISTE.")
