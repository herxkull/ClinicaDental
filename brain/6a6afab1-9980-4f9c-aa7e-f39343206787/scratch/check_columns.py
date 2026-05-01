import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='pelusmi' AND table_name='gestion_cita'")
print("Columnas de pelusmi.gestion_cita:", [r[0] for r in cursor.fetchall()])
