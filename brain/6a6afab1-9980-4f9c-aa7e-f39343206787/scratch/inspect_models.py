import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import inspect
from django.apps import apps

gestion_models = apps.get_app_config('gestion').get_models()
for m in gestion_models:
    print(f"Model: {m.__name__}")
    for name, field in m._meta.fields_map.items():
        print(f"  Field: {name}")
