import os
import sys
import django

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica

clinicas = Clinica.objects.all()
if clinicas.exists():
    for c in clinicas:
        print(f"CLINICA_ENCONTRADA:{c.schema_name}")
else:
    print("NO_HAY_CLINICAS")
