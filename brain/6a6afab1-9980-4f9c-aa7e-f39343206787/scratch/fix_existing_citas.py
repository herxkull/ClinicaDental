import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from clientes.models import Clinica
from gestion.models import Cita, DoctorColaborador

tenants = Clinica.objects.exclude(schema_name='public')
for t in tenants:
    with schema_context(t.schema_name):
        julian = DoctorColaborador.objects.filter(nombre__icontains='Julian Estrada').first()
        if not julian:
            julian = DoctorColaborador.objects.first()
            
        if julian:
            # Asignar a Julian Estrada las citas que no tienen doctor asignado
            citas_sin_doc = Cita.objects.filter(doctor__isnull=True)
            for c in citas_sin_doc:
                c.doctor = julian
                c.save()
            print(f"✅ Tenant {t.schema_name}: Se asignó el Dr. {julian.nombre} a {citas_sin_doc.count()} citas que estaban sin doctor.")
