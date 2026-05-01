import os, sys, django
from django.utils import timezone
import random
from decimal import Decimal

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from gestion.models import Paciente, Tratamiento, Producto, Pago

# Cambiar al esquema pelusmi
with schema_context('pelusmi'):
    print("Limpiando datos previos en pelusmi...")
    Pago.objects.all().delete()
    Paciente.objects.all().delete()
    Tratamiento.objects.all().delete()
    Producto.objects.all().delete()

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
        Producto.objects.create(nombre="Agujas Cortas 27G", categoria="Materiales", descripcion="Caja de 100 agujas.", cantidad_actual=12, stock_minimo=4, costo_unitario=Decimal("11.50"), precio_venta_sugerido=Decimal("15.00")),
    ]

    print("Creando 20 clientes (pacientes) y sus pagos...")
    nombres = [
        "Alejandro Gómez", "Beatriz López", "Carlos Mendoza", "Diana Torres",
        "Eduardo Ríos", "Fernanda Ortiz", "Gabriel Cruz", "Helena Vargas",
        "Iván Castro", "Julia Peña", "Kevin Soto", "Laura Moreno",
        "Mauricio Silva", "Natalia Reyes", "Oscar Paredes", "Patricia Morales",
        "Ricardo Franco", "Sofía Medina", "Tomás Herrera", "Valeria Rojas"
    ]

    # Crear una fecha base en el mes actual para los gráficos
    now = timezone.now()

    for i, nombre in enumerate(nombres):
        paciente = Paciente.objects.create(
            nombre=nombre,
            cedula=f"001-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}A",
            fecha_nacimiento="1990-05-15",
            telefono=f"8888-{1111 + i}",
            email=f"paciente{i}@test.com"
        )

        # Crear entre 1 y 3 pagos por cliente para que las gráficas tengan volumen de datos
        num_pagos = random.randint(1, 3)
        for p_idx in range(num_pagos):
            # Variar las fechas para tener un historial de transacciones en los últimos 15 días
            dia_pago = random.randint(1, 28)
            fecha_pago = now.replace(day=dia_pago, hour=10, minute=0, second=0)

            # Seleccionar un tratamiento aleatorio para el monto
            tr = random.choice(tratamientos)
            
            Pago.objects.create(
                paciente=paciente,
                monto=tr.precio_venta,
                monto_recibido=tr.precio_venta,
                metodo=random.choice(['EFECTIVO', 'TRANSFERENCIA', 'TARJETA']),
                fecha=fecha_pago,
                notas=f"Pago por {tr.nombre}"
            )

    print("¡Proceso completado satisfactoriamente!")
