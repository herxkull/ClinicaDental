import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Dominio, Clinica

# 1. Obtener los tenants involucrados
public_tenant = Clinica.objects.get(schema_name='public')
hersan_tenant = Clinica.objects.get(schema_name='hersandental')

# 2. Corregir el dominio 'localhost'
print("Corrigiendo dominios...")

# Eliminar el localhost mal asignado
Dominio.objects.filter(domain='localhost', tenant=hersan_tenant).delete()

# Asegurar que localhost esté en public
Dominio.objects.get_or_create(domain='localhost', tenant=public_tenant, defaults={'is_primary': True})

# También aseguramos que hersan use hersan.localhost
Dominio.objects.get_or_create(domain='hersan.localhost', tenant=hersan_tenant, defaults={'is_primary': True})

print("¡Listo! Dominios reconfigurados.")
