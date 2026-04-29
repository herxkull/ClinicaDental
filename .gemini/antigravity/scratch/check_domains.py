import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica, Dominio

def check_setup():
    print("--- DIAGNÓSTICO DE TENANTS Y DOMINIOS ---")
    clinicas = Clinica.objects.all()
    for c in clinicas:
        print(f"\n[Clínica: {c.nombre_clinica} | Esquema: {c.schema_name}]")
        dominios = Dominio.objects.filter(tenant=c)
        if not dominios:
            print("  (!) No tiene dominios asociados.")
        for d in dominios:
            primary = "*" if d.is_primary else " "
            print(f"  {primary} Dominio: {d.domain}")

if __name__ == "__main__":
    check_setup()
