import os
import sys
import django

# Añadir el directorio actual al path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica, Dominio
c = Clinica.objects.filter(schema_name='roeden').first()
with open('domain_debug.txt', 'w') as f:
    f.write(f'Clinica: {c}\n')
    if c:
        doms = [d.domain for d in Dominio.objects.filter(tenant=c)]
        f.write(f'Dominios: {doms}\n')
    else:
        f.write('Clinica no encontrada\n')
