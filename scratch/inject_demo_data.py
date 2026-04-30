import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from gestion.models import Paciente, Tratamiento, Cita, Producto, MovimientoInventario

def inject():
    schema = 'kimet'
    with schema_context(schema):
        print(f"--- INYECTANDO DATOS DE PRUEBA EN: {schema} ---")
        
        # 1. Tratamientos
        tratamientos_data = [
            ('Limpieza Dental', 45.0, '#10b981'),
            ('Calza de Resina', 60.0, '#3b82f6'),
            ('Extracción Simple', 50.0, '#ef4444'),
            ('Ortodoncia (Mensualidad)', 80.0, '#8b5cf6'),
            ('Diseño de Sonrisa', 450.0, '#f59e0b'),
        ]
        tratamientos = []
        for nombre, precio, color in tratamientos_data:
            t, _ = Tratamiento.objects.get_or_create(
                nombre=nombre,
                defaults={'precio_venta': precio, 'color': color, 'descripcion': f'Servicio de {nombre}'}
            )
            tratamientos.append(t)
        print(f"Tratamientos listos: {len(tratamientos)}")

        # 2. Pacientes
        nombres = ['Carlos', 'Maria', 'Jose', 'Ana', 'Luis', 'Sofia', 'Roberto', 'Lucia', 'Miguel', 'Elena', 'David', 'Carmen']
        apellidos = ['Garcia', 'Lopez', 'Martinez', 'Rodriguez', 'Perez', 'Sanchez', 'Gonzalez', 'Torres', 'Ramirez', 'Flores', 'Diaz', 'Vargas']
        
        pacientes = []
        for i in range(12):
            nombre_full = f"{nombres[i]} {apellidos[i]}"
            cedula = f"001-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}A"
            p, _ = Paciente.objects.get_or_create(
                cedula=cedula,
                defaults={
                    'nombre': nombre_full,
                    'telefono': f'8{random.randint(10000000, 99999999)}',
                    'email': f'{nombres[i].lower()}.{apellidos[i].lower()}@ejemplo.com',
                    'fecha_nacimiento': datetime(1980 + random.randint(0, 25), random.randint(1, 12), random.randint(1, 28)).date()
                }
            )
            pacientes.append(p)
        print(f"Pacientes listos: {len(pacientes)}")

        # 3. Inventario
        productos_data = [
            ('Guantes Nitrilo (Caja)', 15, 5, 20),
            ('Resina 3M', 45, 2, 8),
            ('Anestesia (Carpules)', 30, 10, 50),
            ('Mascarillas Quirúrgicas', 10, 5, 100),
            ('Cepillos Profilaxis', 5, 20, 40),
        ]
        for nombre, costo, minimo, actual in productos_data:
            Producto.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'costo_unitario': costo,
                    'stock_minimo': minimo,
                    'cantidad_actual': actual,
                    'descripcion': f'Insumo para clínica: {nombre}'
                }
            )
        print("Inventario listo")

        # 4. Citas (Últimos 60 días)
        print("Generando citas históricas...")
        Cita.objects.all().delete() # Limpiamos para no duplicar en demo
        
        hoy = timezone.now()
        for i in range(40):
            dias_atras = random.randint(0, 60)
            fecha = (hoy - timedelta(days=dias_atras)).date()
            hora = datetime.strptime(f"{random.randint(8, 17)}:00", "%H:%M").time()
            
            p = random.choice(pacientes)
            t = random.choice(tratamientos)
            
            estado = 'COMPLETADA' if dias_atras > 2 else random.choice(['PENDIENTE', 'CONFIRMADA'])
            
            Cita.objects.create(
                paciente=p,
                tratamiento=t,
                fecha=fecha,
                hora=hora,
                motivo=f'Cita de {t.nombre}',
                estado=estado
            )
        print("Citas listas")
        print("--- INYECCION COMPLETADA ---")

if __name__ == "__main__":
    inject()
