
import os
import sys
import django

# Añadir el directorio raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Clinica, Dominio

def fix_domains():
    print("Iniciando actualización de dominios...")
    
    # Listar todas las clínicas para depuración
    clinicas = Clinica.objects.all()
    print(f"Clínicas encontradas: {[c.schema_name for c in clinicas]}")

    # Intentar buscar la clínica hersan
    clinica = Clinica.objects.filter(schema_name='hersan').first()
    
    if not clinica:
        # Si no existe hersan, buscamos la que NO sea public
        clinica = Clinica.objects.exclude(schema_name='public').first()
        
    if not clinica:
        print("Error: No se encontró ninguna clínica de cliente (no public).")
        return

    print(f"Usando clínica: {clinica.nombre_clinica} (Esquema: {clinica.schema_name})")

    # Dominios a asegurar
    dominios_requeridos = [
        'hersan.localhost',
        'hersan.test-clinica.com',
        'hersan.127.0.0.1.nip.io'
    ]

    for d in dominios_requeridos:
        # Primero ver si el dominio ya existe en alguna otra clínica
        existente = Dominio.objects.filter(domain=d).first()
        if existente:
            if existente.tenant == clinica:
                print(f"Dominio ya configurado correctamente: {d}")
            else:
                print(f"Cambiando dominio {d} de {existente.tenant.schema_name} a {clinica.schema_name}")
                existente.tenant = clinica
                existente.save()
        else:
            Dominio.objects.create(tenant=clinica, domain=d)
            print(f"Dominio creado: {d}")

    print("Proceso finalizado con éxito.")

if __name__ == "__main__":
    fix_domains()
