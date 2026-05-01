import os, sys, django
from django.utils import timezone
import random
from decimal import Decimal
import datetime

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from gestion.models import Paciente, Tratamiento, Producto, Pago, Cita, DoctorColaborador

# Cambiar al esquema pelusmi
with schema_context('pelusmi'):
    print("Limpiando datos previos en pelusmi...")
    Pago.objects.all().delete()
    Cita.objects.all().delete()
    Paciente.objects.all().delete()
    Tratamiento.objects.all().delete()
    Producto.objects.all().delete()
    DoctorColaborador.objects.all().delete()

    print("Creando doctor colaborador...")
    doc = DoctorColaborador.objects.create(
        nombre="Dra. Marisol Rivas",
        especialidad="Odontología General",
        telefono="8888-9999",
        email="marisol@pelusmi.com",
        color_agenda="#3b82f6",
        is_active=True
    )

    print("Creando tratamientos...")
    tratamientos = [
        Tratamiento.objects.create(nombre="Limpieza Dental Simple", descripcion="Limpieza profunda con ultrasonido.", precio_venta=Decimal("45.00")),
        Tratamiento.objects.create(nombre="Extracción Molar", descripcion="Extracción dental quirúrgica.", precio_venta=Decimal("80.00")),
        Tratamiento.objects.create(nombre="Ortodoncia Mensualidad", descripcion="Ajuste mensual de brackets.", precio_venta=Decimal("60.00")),
        Tratamiento.objects.create(nombre="Blanqueamiento Láser", descripcion="Sesión completa de blanqueamiento dental.", precio_venta=Decimal("150.00")),
        Tratamiento.objects.create(nombre="Endodoncia Completa", descripcion="Tratamiento de conducto radicular.", precio_venta=Decimal("220.00")),
    ]

    print("Creando productos en inventario...")
    productos = [
        Producto.objects.create(nombre="Guantes Nitrilo (M)", categoria="Descartables", descripcion="Caja de 100 unidades.", cantidad_actual=50, stock_minimo=10, costo_unitario=Decimal("8.50"), precio_venta_sugerido=Decimal("12.00")),
        Producto.objects.create(nombre="Mascarillas Quirúrgicas", categoria="Descartables", descripcion="Caja de 50 unidades.", cantidad_actual=4, stock_minimo=5, costo_unitario=Decimal("4.00"), precio_venta_sugerido=Decimal("6.50")),  # Stock bajo
        Producto.objects.create(nombre="Resina Dental A2", categoria="Materiales", descripcion="Jeringa restaurativa universal.", cantidad_actual=15, stock_minimo=3, costo_unitario=Decimal("18.00"), precio_venta_sugerido=Decimal("25.00")),
        Producto.objects.create(nombre="Anestesia Lidocaína", categoria="Materiales", descripcion="Caja de 50 tubos.", cantidad_actual=2, stock_minimo=3, costo_unitario=Decimal("22.00"), precio_venta_sugerido=Decimal("30.00")),  # Stock bajo
    ]

    print("Creando 20 clientes, citas del mes pasado y sus pagos...")
    nombres = [
        "Carlos Duarte", "Ana Guevara", "Luisa Morales", "Ernesto Chavarría",
        "Rosa María Espinoza", "Héctor Zelaya", "Martha Blandón", "Juan Carlos Rivas",
        "Claudia Mendoza", "Jorge Isaacs", "Silvia Torres", "Roberto Solórzano",
        "Mercedes Reyes", "Ricardo Arjona", "Juana de Arco", "William Wallace",
        "Isabel la Católica", "Napoleón Bonaparte", "Simón Bolívar", "José Martí"
    ]

    # Mes pasado (Abril 2026)
    last_month_year = 2026
    last_month = 4

    for i, nombre in enumerate(nombres):
        paciente = Paciente.objects.create(
            nombre=nombre,
            cedula=f"001-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}A",
            fecha_nacimiento="1988-10-12",
            telefono=f"7777-{2222 + i}",
            email=f"cliente{i}@salud.com"
        )

        tr = random.choice(tratamientos)
        dia_cita = random.randint(1, 28)
        hora_cita = datetime.time(random.randint(8, 17), 0)

        # Crear Cita en el mes pasado
        cita = Cita.objects.create(
            paciente=paciente,
            doctor=doc,
            tratamiento=tr,
            fecha=datetime.date(last_month_year, last_month, dia_cita),
            hora=hora_cita,
            motivo=f"Cita de revisión para {tr.nombre}",
            estado="COMPLETADA"
        )

        # Crear Pago vinculado a esa cita
        fecha_pago = timezone.make_aware(datetime.datetime(last_month_year, last_month, dia_cita, 11, 0, 0))
        Pago.objects.create(
            paciente=paciente,
            monto=tr.precio_venta,
            monto_recibido=tr.precio_venta,
            metodo=random.choice(['EFECTIVO', 'TRANSFERENCIA', 'TARJETA']),
            cita=cita,
            fecha=fecha_pago,
            notas=f"Pago completado por {tr.nombre}"
        )

    print("¡Proceso de inyección con citas completadas exitosamente!")
