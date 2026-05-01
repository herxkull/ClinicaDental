import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from clientes.models import Clinica
from gestion.models import Cita, DoctorColaborador

tenants = Clinica.objects.exclude(schema_name='public')
for t in tenants:
    print(f"\n=================== TENANT: {t.schema_name} ===================")
    with schema_context(t.schema_name):
        doctores = DoctorColaborador.objects.all()
        print("--- Doctores ---")
        for d in doctores:
            print(f"ID: {d.id}, Nombre: {d.nombre}, Color: {d.color_agenda}")
            
        citas = Cita.objects.all()
        print("\n--- Citas ---")
        for c in citas:
            doctor_nombre = c.doctor.nombre if c.doctor else "Sin doctor"
            print(f"Cita ID: {c.id}, Paciente: {c.paciente.nombre}, Doctor: {doctor_nombre}, Color: {c.doctor.color_agenda if c.doctor else 'N/A'}")
