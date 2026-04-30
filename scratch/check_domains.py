import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Dominio, Clinica

print("--- Listado de Dominios ---")
for d in Dominio.objects.all():
    print(f"Domain: {d.domain} | Tenant: {d.tenant.schema_name} | Primary: {d.is_primary}")

# Verificamos si localhost está en el lugar equivocado
base_domain = "localhost"
wrong_domains = Dominio.objects.filter(domain=base_domain).exclude(tenant__schema_name='public')

if wrong_domains.exists():
    print(f"\n[ALERTA] Se encontraron {wrong_domains.count()} dominios '{base_domain}' mal asignados.")
    # No lo corregimos automáticamente sin estar seguros, pero informamos.
