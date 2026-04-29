import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Dominio

def fix_domains():
    print("--- CORRIGIENDO PUERTOS EN DOMINIOS ---")
    dominios = Dominio.objects.all()
    for d in dominios:
        if ":8000" not in d.domain:
            old_domain = d.domain
            d.domain = f"{old_domain}:8000"
            d.save()
            print(f"ACTUALIZADO: '{old_domain}' -> '{d.domain}'")
        else:
            print(f"OMITIDO: '{d.domain}' ya tiene puerto.")
    print("\n¡Listo! Todos los dominios ahora incluyen el puerto :8000")

if __name__ == "__main__":
    fix_domains()
