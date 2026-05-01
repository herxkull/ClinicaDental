import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica, Dominio
clinicas = Clinica.objects.all()
with open('all_domains_debug.txt', 'w') as f:
    for c in clinicas:
        doms = [d.domain for d in Dominio.objects.filter(tenant=c)]
        f.write(f'Clinica: {c.schema_name} -> {doms}\n')
