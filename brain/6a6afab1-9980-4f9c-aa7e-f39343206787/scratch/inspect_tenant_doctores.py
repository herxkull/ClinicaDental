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
        doctores = DoctorColaborador.objects.all()
        print(f"\n===== TENANT: {t.schema_name} =====")
        for d in doctores:
            print(f"Doctor ID: {d.id} | Nombre: {d.nombre} | Color: {d.color_agenda}")
        citas = Cita.objects.all().order_by('-id')[:5]
        for c in citas:
            print(f"Cita ID: {c.id} | Paciente: {c.paciente.nombre} | Doctor: {c.doctor.nombre if c.doctor else 'Ninguno'}")
