from django.shortcuts import render, get_object_or_404, redirect
from .models import Paciente, Cita, Tratamiento, Pago, ArchivoPaciente, Receta, Producto, MaterialTratamiento
from datetime import date
from .forms import PacienteForm, CitaForm, DienteEstadoForm, DienteEstado, TratamientoForm, PagoForm, ArchivoPacienteForm, RecetaForm
from django.db.models import Sum, Q, Count, F
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import json
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
import openpyxl
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
@login_required
def dashboard(request):
    # Usamos timezone.now() para asegurar la hora local configurada
    hoy = timezone.now().date()

    # --- 1. Datos de Citas y Pacientes ---
    total_pacientes = Paciente.objects.count()
    citas_hoy_lista = Cita.objects.filter(fecha=hoy).order_by('hora')
    citas_hoy_count = citas_hoy_lista.count()
    alertas_inventario = Producto.objects.filter(cantidad_actual__lte=F('stock_minimo')).count()

    # --- 2. Lógica Financiera ---
    # Ingresos esperados SOLO de hoy
    ingresos_esperados = citas_hoy_lista.aggregate(total=Sum('tratamiento__costo_base'))['total'] or 0

    # Ingresos Totales Históricos
    ingresos_totales = Pago.objects.aggregate(total=Sum('monto'))['total'] or 0

    # Cuentas por Cobrar (Total de todos los servicios - Total pagado)
    total_servicios = Cita.objects.aggregate(total=Sum('tratamiento__costo_base'))['total'] or 0
    cuentas_por_cobrar = total_servicios - ingresos_totales

    # --- 3. Otros Datos ---
    ultimos_pacientes = Paciente.objects.all().order_by('-id')[:5]

    # --- 4. Lógica para el Gráfico ---
    datos_tratamientos = Cita.objects.values('tratamiento__nombre').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')

    labels_grafico = [item['tratamiento__nombre'] for item in datos_tratamientos]
    data_grafico = [item['cantidad'] for item in datos_tratamientos]

    # --- 5. UN SOLO CONTEXTO (Sin sobrescribir) ---
    context = {
        'total_pacientes': total_pacientes,
        'citas_hoy': citas_hoy_count,
        'citas_hoy_lista': citas_hoy_lista,
        'ingresos_esperados': ingresos_esperados,
        'ultimos_pacientes': ultimos_pacientes,
        'ingresos_totales': ingresos_totales,
        'cuentas_por_cobrar': cuentas_por_cobrar,
        'labels_grafico': json.dumps(labels_grafico),
        'data_grafico': json.dumps(data_grafico),
        'alertas_inventario': alertas_inventario,
    }

    return render(request, 'gestion/dashboard.html', context)


def completar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    # Cambiamos el estado al contrario (Si es True pasa a False, y viceversa)
    cita.completada = not cita.completada
    cita.save()

    # Redirige a la página anterior (así funciona desde el dashboard o desde la lista de citas)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
# Vista para listar pacientes
@login_required
def lista_pacientes(request):
    query = request.GET.get('q')

    # 1. Obtenemos la lista completa (con o sin búsqueda)
    if query:
        pacientes_lista = Paciente.objects.filter(
            Q(nombre__icontains=query) | Q(cedula__icontains=query)
        ).order_by('nombre')
    else:
        pacientes_lista = Paciente.objects.all().order_by('nombre')

    # 2. Configuramos el Paginador (ej. 10 pacientes por página)
    paginator = Paginator(pacientes_lista, 10)

    # 3. Obtenemos el número de página actual de la URL (ej. ?page=2)
    page_number = request.GET.get('page')

    # 4. Le pedimos al paginador que nos dé solo los pacientes de esa página
    pacientes = paginator.get_page(page_number)

    return render(request, 'gestion/lista_pacientes.html', {
        'pacientes': pacientes,
        'query': query
    })
# Vista para registrar paciente
def nuevo_paciente(request):
    if request.method == "POST":
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_pacientes')
    else:
        form = PacienteForm()
    return render(request, 'gestion/paciente_form.html', {'form': form})


def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        # 'instance' es el truco para que Django sepa que es una edición
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            return redirect('detalle_paciente', pk=paciente.pk)
    else:
        form = PacienteForm(instance=paciente)

    return render(request, 'gestion/paciente_form.html', {
        'form': form,
        'editando': True  # Pasamos esta variable para cambiar el título en el HTML
    })

def lista_citas(request):
    citas = Cita.objects.all().order_by('fecha', 'hora')
    return render(request, 'gestion/lista_citas.html', {'citas': citas})

def nueva_cita(request):
    if request.method == "POST":
        form = CitaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_citas')
    else:
        form = CitaForm()
    return render(request, 'gestion/cita_form.html', {'form': form})


def detalle_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    citas = Cita.objects.filter(paciente=paciente).order_by('-fecha')

    # --- LÓGICA DEL ODONTOGRAMA ---
    dientes_registrados = paciente.odontograma.all()
    diccionario_dientes = {
        str(d.numero_diente): (d.estado or "SANO")
        for d in dientes_registrados
        if d.numero_diente is not None
    }

    # --- LÓGICA FINANCIERA (CORREGIDA) ---
    # Calculamos el total recorriendo las citas para evitar errores de agregación con Nulos
    total_tratamientos = 0
    for cita in citas:
        if cita.tratamiento and cita.tratamiento.costo_base:
            total_tratamientos += cita.tratamiento.costo_base

    pagos = Pago.objects.filter(paciente=paciente).order_by('-fecha')
    total_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0
    saldo_pendiente = float(total_tratamientos) - float(total_pagos)

    return render(request, 'gestion/detalle_paciente.html', {
        'paciente': paciente,
        'citas': citas,
        'dientes_detalle': dientes_registrados,
        'estados_dientes_json': json.dumps(diccionario_dientes),
        'total_tratamientos': total_tratamientos,
        'total_pagos': total_pagos,
        'saldo_pendiente': saldo_pendiente,
        'pagos': pagos
    })

def lista_tratamientos(request):
    # prefetch_related hace que cargue los materiales rápido y sin sobrecargar la base de datos
    tratamientos = Tratamiento.objects.prefetch_related('materiales__producto').all().order_by('nombre')
    productos = Producto.objects.all().order_by('nombre')

    return render(request, 'gestion/lista_tratamientos.html', {
        'tratamientos': tratamientos,
        'productos': productos
    })

@login_required
@require_POST
def guardar_tratamiento(request):
    tratamiento_id = request.POST.get('tratamiento_id')
    nombre = request.POST.get('nombre')
    descripcion = request.POST.get('descripcion', '')
    costo_base = request.POST.get('costo_base', 0)

    # 1. Crear o Editar el Tratamiento
    if tratamiento_id: # Si tiene ID, estamos editando
        tratamiento = get_object_or_404(Tratamiento, pk=tratamiento_id)
        tratamiento.nombre = nombre
        tratamiento.descripcion = descripcion
        tratamiento.costo_base = costo_base
        tratamiento.save()
        # Borramos los materiales viejos para reemplazarlos por los nuevos que vengan en el form
        MaterialTratamiento.objects.filter(tratamiento=tratamiento).delete()
    else: # Si no tiene ID, es uno nuevo
        tratamiento = Tratamiento.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            costo_base=costo_base
        )

    # 2. Procesar la lista de Materiales (Vienen en forma de listas desde el HTML)
    productos_ids = request.POST.getlist('producto_id[]')
    cantidades = request.POST.getlist('cantidad[]')

    # Usamos zip para emparejar el ID del producto con su cantidad
    for p_id, cant in zip(productos_ids, cantidades):
        if p_id and cant and int(cant) > 0:
            producto = get_object_or_404(Producto, pk=p_id)
            MaterialTratamiento.objects.create(
                tratamiento=tratamiento,
                producto=producto,
                cantidad_usada=int(cant)
            )

    return redirect('lista_tratamientos')
def gestionar_tratamiento(request, pk=None):
    # Si recibimos un 'pk' (ID), buscamos el tratamiento para editarlo. Si no, creamos uno en blanco.
    if pk:
        tratamiento = get_object_or_404(Tratamiento, pk=pk)
        titulo = f"Editar Tratamiento: {tratamiento.nombre}"
    else:
        tratamiento = None
        titulo = "Nuevo Tratamiento"

    if request.method == "POST":
        form = TratamientoForm(request.POST, instance=tratamiento)
        if form.is_valid():
            form.save()
            return redirect('lista_tratamientos')
    else:
        form = TratamientoForm(instance=tratamiento)

    return render(request, 'gestion/tratamiento_form.html', {'form': form, 'titulo': titulo})


def registrar_pago(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == "POST":
        form = PagoForm(request.POST)
        if form.is_valid():
            # No guardamos directamente porque nos falta asignarle el paciente
            pago = form.save(commit=False)
            pago.paciente = paciente
            pago.save()
            return redirect('detalle_paciente', pk=paciente.pk)
    else:
        form = PagoForm()

    return render(request, 'gestion/pago_form.html', {'form': form, 'paciente': paciente})


@login_required
def subir_archivo(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == "POST":
        # ¡IMPORTANTE! request.FILES es necesario para procesar archivos
        form = ArchivoPacienteForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.save(commit=False)
            archivo.paciente = paciente
            archivo.save()
            return redirect('detalle_paciente', pk=paciente.pk)
    else:
        form = ArchivoPacienteForm()

    return render(request, 'gestion/archivo_form.html', {'form': form, 'paciente': paciente})


@login_required
def calendario(request):
    # Traemos los pacientes y tratamientos para llenar los desplegables del modal
    pacientes = Paciente.objects.all().order_by('nombre')
    tratamientos = Tratamiento.objects.all().order_by('nombre')

    return render(request, 'gestion/calendario.html', {
        'pacientes': pacientes,
        'tratamientos': tratamientos
    })


@login_required
@require_POST
def guardar_cita_calendario(request):
    paciente_id = request.POST.get('paciente')
    tratamiento_id = request.POST.get('tratamiento')
    fecha = request.POST.get('fecha')
    hora = request.POST.get('hora')
    motivo = request.POST.get('motivo')

    paciente = get_object_or_404(Paciente, pk=paciente_id)
    tratamiento = get_object_or_404(Tratamiento, pk=tratamiento_id) if tratamiento_id else None

    # Creamos la cita
    Cita.objects.create(
        paciente=paciente,
        tratamiento=tratamiento,
        fecha=fecha,
        hora=hora,
        motivo=motivo
    )

    # Recargamos el calendario para ver la nueva cita inmediatamente
    return redirect('calendario')

@login_required
def citas_json(request):
    citas = Cita.objects.all()
    eventos = []

    for cita in citas:
        # FullCalendar necesita un formato ISO (YYYY-MM-DDTHH:MM:SS)
        start_dt = f"{cita.fecha.isoformat()}T{cita.hora.strftime('%H:%M:%S')}"

        # LA MAGIA ESTÁ AQUÍ: Si no hay tratamiento, ponemos un texto por defecto
        nombre_tratamiento = cita.tratamiento.nombre if cita.tratamiento else "Consulta General"

        eventos.append({
            'title': f"{cita.paciente.nombre} ({nombre_tratamiento})",
            'start': start_dt,
            'url': reverse('detalle_paciente', args=[cita.paciente.pk]),
            # Color dinámico: verde si está completada, azul si está pendiente
            'backgroundColor': '#198754' if cita.completada else '#0d6efd',
            'borderColor': '#198754' if cita.completada else '#0d6efd',
        })

    return JsonResponse(eventos, safe=False)
@login_required
def nueva_receta(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == "POST":
        form = RecetaForm(request.POST)
        if form.is_valid():
            receta = form.save(commit=False)
            receta.paciente = paciente
            receta.save()
            # ¡Magia! Al guardar, redireccionamos directo a la vista de imprimir
            return redirect('imprimir_receta', pk=receta.pk)
    else:
        form = RecetaForm()

    return render(request, 'gestion/receta_form.html', {'form': form, 'paciente': paciente})


@login_required
def imprimir_receta(request, pk):
    # Esta vista NO usará el base.html normal, será una página en blanco limpia
    receta = get_object_or_404(Receta, pk=pk)
    return render(request, 'gestion/receta_imprimir.html', {'receta': receta})


@login_required
def exportar_pacientes_excel(request):
    # 1. Crear el libro y la hoja de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte de Pacientes"

    # 2. Definir los encabezados
    headers = ['Nombre Completo', 'Cédula', 'Teléfono', 'Total Cargos', 'Total Pagado', 'Saldo Pendiente']
    ws.append(headers)

    # 3. Obtener los datos y escribirlos
    pacientes = Paciente.objects.all()
    for p in pacientes:
        # Reutilizamos la lógica de cálculos que hicimos para el detalle
        cargos = p.cita_set.aggregate(total=Sum('tratamiento__costo_base'))['total'] or 0
        pagos = p.pagos.aggregate(total=Sum('monto'))['total'] or 0
        saldo = cargos - pagos

        ws.append([p.nombre, p.cedula, p.telefono, cargos, pagos, saldo])

    # 4. Configurar la respuesta del navegador para descargar el archivo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Pacientes_Hersan.xlsx"'

    wb.save(response)
    return response


@login_required
def estado_cuenta_pdf(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    # Obtenemos todas las citas con tratamiento (Cargos)
    cargos = Cita.objects.filter(paciente=paciente).order_by('fecha')

    # Obtenemos todos los pagos (Abonos)
    abonos = Pago.objects.filter(paciente=paciente).order_by('fecha')

    # Calculamos totales
    total_cargos = cargos.aggregate(total=Sum('tratamiento__costo_base'))['total'] or 0
    total_abonos = abonos.aggregate(total=Sum('monto'))['total'] or 0
    saldo_pendiente = total_cargos - total_abonos

    context = {
        'paciente': paciente,
        'cargos': cargos,
        'abonos': abonos,
        'total_cargos': total_cargos,
        'total_abonos': total_abonos,
        'saldo_pendiente': saldo_pendiente,
        'fecha_emision': date.today(),
    }
    return render(request, 'gestion/estado_cuenta_imprimir.html', context)


@login_required
def inventario(request):
    productos = Producto.objects.all().order_by('nombre')

    # Estadísticas para las tarjetas superiores
    total_productos = productos.count()
    productos_bajos = productos.filter(cantidad_actual__lte=F('stock_minimo')).count()

    # Calcular el valor total del inventario actual
    valor_inventario = sum(p.cantidad_actual * p.precio_compra for p in productos)

    context = {
        'productos': productos,
        'total_productos': total_productos,
        'productos_bajos': productos_bajos,
        'valor_inventario': valor_inventario,
        'alertas': productos_bajos > 0, # ¡Clave para que aparezca la alerta roja!
    }
    # Apuntamos al HTML correcto
    return render(request, 'gestion/inventario.html', context)


@login_required
@require_POST
def crear_producto(request):
    # Recibimos los datos del formulario HTML
    nombre = request.POST.get('nombre')
    descripcion = request.POST.get('descripcion', '')
    cantidad = request.POST.get('cantidad_actual', 0)
    minimo = request.POST.get('stock_minimo', 5)
    precio = request.POST.get('precio_compra', 0.00)

    # Creamos el registro en la base de datos
    Producto.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        cantidad_actual=cantidad,
        stock_minimo=minimo,
        precio_compra=precio
    )

    # Redirigimos de vuelta a la página del inventario
    return redirect('inventario')
@login_required
def aumentar_stock(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.cantidad_actual += 1
    producto.save()
    return redirect('inventario')

@login_required
def disminuir_stock(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if producto.cantidad_actual > 0:
        producto.cantidad_actual -= 1
        producto.save()
    return redirect('inventario')


@login_required
def finalizar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)

    if not cita.completada:
        # 1. Cambiar el booleano correcto
        cita.completada = True
        cita.save()

        # 2. Descontar materiales (si existen)
        materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento)

        for item in materiales:
            producto = item.producto
            if producto.cantidad_actual >= item.cantidad_usada:
                producto.cantidad_actual -= item.cantidad_usada
                producto.save()
                messages.success(request, f"Se descontó {item.cantidad_usada} de {producto.nombre}.")
            else:
                messages.warning(request, f"Stock insuficiente de {producto.nombre}.")

    return redirect('dashboard')


@login_required
@require_POST
def actualizar_diente(request, paciente_id):
    try:
        data = json.loads(request.body)  # Leemos los datos enviados por JavaScript (AJAX)
        numero_diente = data.get('numero_diente')
        nuevo_estado = data.get('estado')
        notas = data.get('notas', '')

        paciente = get_object_or_404(Paciente, pk=paciente_id)

        # update_or_create: Si existe lo actualiza, si no, lo crea. ¡Súper útil!
        diente, created = DienteEstado.objects.update_or_create(
            paciente=paciente,
            numero_diente=numero_diente,
            defaults={'estado': nuevo_estado, 'notas': notas}
        )

        return JsonResponse({
            'status': 'ok',
            'message': f'Diente {numero_diente} actualizado a {diente.get_estado_display()}',
            'nuevo_estado': nuevo_estado
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
# Create your views here.
