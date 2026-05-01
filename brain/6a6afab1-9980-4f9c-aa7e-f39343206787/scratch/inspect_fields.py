import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
m_list = ['Paciente', 'Tratamiento', 'Producto', 'Pago']
for m_name in m_list:
    m = apps.get_model('gestion', m_name)
    print(f"--- Model {m_name} ---")
    for f in m._meta.get_fields():
        if f.is_relation and f.one_to_many: continue
        print(f" Name: {f.name} (Type: {type(f).__name__})")
