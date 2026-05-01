import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from clientes.models import Clinica, Suscripcion
from django.utils import timezone

c = Clinica.objects.get(schema_name='pelusmi')
s = c.suscripciones.first()
if s:
    s.estado_pago = 'APROBADO'
    s.fecha_vencimiento = timezone.now() + timezone.timedelta(days=30)
    s.save()
    print(f"Suscripción de la clínica '{c.nombre_clinica}' actualizada a APROBADO exitosamente.")
