import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())
django.setup()

from clientes.models import Dominio

def clean_ports():
    print("--- Limpiando puertos de la tabla de Dominios ---")
    dominios = Dominio.objects.all()
    for d in dominios:
        if ':' in d.domain:
            new_domain = d.domain.split(':')[0]
            print(f"Modificando: {d.domain} -> {new_domain}")
            
            # Verificar si ya existe el dominio sin puerto para evitar duplicados
            if Dominio.objects.filter(domain=new_domain).exclude(id=d.id).exists():
                print(f"[ELIMINANDO] Duplicado detectado para {new_domain}")
                d.delete()
            else:
                d.domain = new_domain
                d.save()
    print("¡Limpieza completada!")

if __name__ == "__main__":
    clean_ports()
