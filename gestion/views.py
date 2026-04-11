import json
from datetime import date, datetime, time
import openpyxl
from .utils import render_to_pdf
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count, F
from .decorators import grupo_requerido
from .models import Paciente, Cita, Tratamiento, Pago, ArchivoPaciente, Receta, Producto, MaterialTratamiento
from .forms import PacienteForm, CitaForm, TratamientoForm, PagoForm, ArchivoPacienteForm, RecetaForm


# ==========================================
# 1. DASHBOARD PRINCIPAL
# ==========================================

@login_required
def dashboard(request):
    hoy = timezone.localtime(timezone.now()).date()
    total_pacientes = Paciente.objects.count()
    citas_hoy_lista = Cita.objects.filter(fecha=hoy).order_by('fecha')
    citas_hoy_count = citas_hoy_lista.count()
    alertas_inventario = Producto.objects.filter(cantidad_actual__lte=F('stock_minimo')).count()

    ingresos_esperados = citas_hoy_lista.aggregate(total=Sum('tratamiento__costo_base'))['total'] or 0
    ingresos_totales = Pago.objects.aggregate(total=Sum('monto'))['total'] or 0

    total_servicios = Cita.objects.aggregate(total=Sum('tratamiento__costo_base'))['total'] or 0
    cuentas_por_cobrar = float(total_servicios) - float(ingresos_totales)

    ultimos_pacientes = Paciente.objects.all().order_by('-id')

    datos_tratamientos = Cita.objects.values('tratamiento__nombre').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')

    labels_grafico = [item['tratamiento__nombre'] for item in datos_tratamientos]
    data_grafico = [item['cantidad'] for item in datos_tratamientos]

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


# ==========================================
# 2. MÓDULO DE PACIENTES
# ==========================================

@login_required
def lista_pacientes(request):
    query = request.GET.get('q')
    if query:
        pacientes_lista = Paciente.objects.filter(
            Q(nombre__icontains=query) | Q(cedula__icontains=query)
        ).order_by('nombre')
    else:
        pacientes_lista = Paciente.objects.all().order_by('nombre')

    paginator = Paginator(pacientes_lista, 10)
    page_number = request.GET.get('page')
    pacientes = paginator.get_page(page_number)

    return render(request, 'gestion/lista_pacientes.html', {'pacientes': pacientes, 'query': query})


@login_required
def detalle_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    citas = Cita.objects.filter(paciente=paciente).order_by('-fecha')

    diccionario_dientes = paciente.odontograma_data if paciente.odontograma_data else {}

    total_tratamientos = 0
    for cita in citas:
        if cita.tratamiento and cita.tratamiento.costo_base:
            total_tratamientos += cita.tratamiento.costo_base

    pagos = Pago.objects.filter(paciente=paciente).order_by('-fecha')
    total_pagos = pagos.aggregate(total=Sum('monto')).get('total') or 0
    saldo_pendiente = float(total_tratamientos) - float(total_pagos)

    return render(request, 'gestion/detalle_paciente.html', {
        'paciente': paciente,
        'citas': citas,
        'dientes_detalle': [],
        'estados_dientes_json': json.dumps(diccionario_dientes),
        'total_tratamientos': total_tratamientos,
        'total_pagos': total_pagos,
        'saldo_pendiente': saldo_pendiente,
        'pagos': pagos
    })


@login_required
def modal_paciente(request, pk=None):
    if pk:
        paciente = get_object_or_404(Paciente, pk=pk)
        titulo = "Editar Paciente"
    else:
        paciente = None
        titulo = "Nuevo Paciente"

    if request.method == "POST":
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'ok'})
        else:
            html_form = render_to_string('gestion/includes/form_paciente_modal.html', {
                'form': form, 'paciente': paciente, 'titulo': titulo
            }, request=request)
            return JsonResponse({'status': 'error', 'html_form': html_form})

    form = PacienteForm(instance=paciente)
    html_form = render_to_string('gestion/includes/form_paciente_modal.html', {
        'form': form, 'paciente': paciente, 'titulo': titulo
    }, request=request)
    return JsonResponse({'html_form': html_form})


@login_required
def subir_archivo(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
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
@grupo_requerido('Doctor') # <--- PROTEGIDO
def exportar_pacientes_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte de Pacientes"

    headers = ['Nombre Completo', 'Cédula', 'Teléfono', 'Total Cargos', 'Total Pagado', 'Saldo Pendiente']
    ws.append(headers)

    pacientes = Paciente.objects.all()
    for p in pacientes:
        cargos = p.cita_set.aggregate(total=Sum('tratamiento__costo_base'))['total'] or 0
        pagos = p.pagos.aggregate(total=Sum('monto'))['total'] or 0
        saldo = cargos - pagos
        ws.append([p.nombre, p.cedula, p.telefono, cargos, pagos, saldo])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Pacientes_Hersan.xlsx"'
    wb.save(response)
    return response


@login_required
def estado_cuenta_pdf(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    cargos = Cita.objects.filter(paciente=paciente).order_by('fecha')
    abonos = Pago.objects.filter(paciente=paciente).order_by('fecha')

    total_cargos = cargos.aggregate(total=Sum('tratamiento__costo_base')).get('total') or 0
    total_abonos = abonos.aggregate(total=Sum('monto')).get('total') or 0
    saldo_pendiente = float(total_cargos) - float(total_abonos)

    context = {
        'paciente': paciente, 'cargos': cargos, 'abonos': abonos,
        'total_cargos': total_cargos, 'total_abonos': total_abonos,
        'saldo_pendiente': saldo_pendiente, 'fecha_emision': date.today(),
    }

    pdf_response = render_to_pdf('gestion/estado_cuenta_imprimir.html', context)

    if pdf_response:
        nombre_archivo = f"Estado_Cuenta_{paciente.nombre.replace(' ', '_')}.pdf"
        pdf_response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
        return pdf_response

    return HttpResponse("Error al generar el PDF del estado de cuenta.")


# ==========================================
# 3. ODONTOGRAMA Y RECETAS
# ==========================================

@login_required
@grupo_requerido('Doctor') # <--- PROTEGIDO (Sólo doctor escribe en el JSON masivo)
def api_odontograma(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            paciente.odontograma_data = data
            paciente.save()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    data = paciente.odontograma_data if paciente.odontograma_data else {}
    return JsonResponse(data)


@login_required
@grupo_requerido('Doctor') # <--- PROTEGIDO (Clínico)
@require_POST
def actualizar_diente(request, paciente_id):
    try:
        data = json.loads(request.body)
        numero_diente = str(data.get('numero_diente'))
        nuevo_estado = data.get('estado')

        paciente = get_object_or_404(Paciente, pk=paciente_id)

        odontograma = paciente.odontograma_data if paciente.odontograma_data else {}
        odontograma[numero_diente] = nuevo_estado
        paciente.odontograma_data = odontograma
        paciente.save()

        return JsonResponse({
            'status': 'ok',
            'message': f'Diente {numero_diente} actualizado',
            'nuevo_estado': nuevo_estado
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@grupo_requerido('Doctor') # <--- PROTEGIDO (Médico)
def nueva_receta(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        form = RecetaForm(request.POST)
        if form.is_valid():
            receta = form.save(commit=False)
            receta.paciente = paciente
            receta.save()
            return redirect('imprimir_receta', pk=receta.pk)
    else:
        form = RecetaForm()
    return render(request, 'gestion/receta_form.html', {'form': form, 'paciente': paciente})


@login_required
def imprimir_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)

    pdf_response = render_to_pdf('gestion/receta_imprimir.html', {'receta': receta})

    if pdf_response:
        nombre_archivo = f"Receta_{receta.paciente.nombre.replace(' ', '_')}.pdf"
        pdf_response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
        return pdf_response

    return HttpResponse("Error al generar el PDF de la receta.")


# ==========================================
# 4. MÓDULO DE CITAS Y CALENDARIO
# ==========================================

@login_required
def lista_citas(request):
    citas = Cita.objects.all().order_by('fecha', 'hora')
    return render(request, 'gestion/lista_citas.html', {'citas': citas})


@login_required
def calendario(request):
    pacientes = Paciente.objects.all().order_by('nombre')
    tratamientos = Tratamiento.objects.all().order_by('nombre')
    return render(request, 'gestion/calendario.html', {'pacientes': pacientes, 'tratamientos': tratamientos})


@login_required
def citas_json(request):
    citas = Cita.objects.all()
    eventos = []

    for cita in citas:
        start_dt = f"{cita.fecha.isoformat()}T{cita.hora.strftime('%H:%M:%S')}"
        nombre_tratamiento = cita.tratamiento.nombre if cita.tratamiento else "Consulta General"

        eventos.append({
            'title': f"{cita.paciente.nombre} ({nombre_tratamiento})",
            'start': start_dt,
            'url': reverse('detalle_paciente', args=[cita.paciente.pk]),
            'backgroundColor': '#198754' if cita.completada else '#0d6efd',
            'borderColor': '#198754' if cita.completada else '#0d6efd',
        })

    return JsonResponse(eventos, safe=False)


@login_required
def nueva_cita(request):
    if request.method == "POST":
        form = CitaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = CitaForm()
    return render(request, 'gestion/cita_form.html', {'form': form})


@login_required
def modal_nueva_cita(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == "POST":
        data = request.POST.copy()
        if not data.get('motivo'):
            data['motivo'] = "Consulta programada"

        form = CitaForm(data)

        if 'paciente' in form.errors:
            del form.errors
        if 'motivo' in form.errors:
            del form.errors

        if form.is_valid():
            cita = form.save(commit=False)
            cita.paciente = paciente
            if not cita.motivo:
                cita.motivo = "Consulta programada"
            cita.save()
            return JsonResponse({'status': 'ok'})

        html_form = render_to_string('gestion/includes/form_cita_modal.html', {'form': form, 'paciente': paciente},
                                     request=request)
        return JsonResponse({'status': 'error', 'html_form': html_form})

    form = CitaForm(initial={'paciente': paciente})
    html_form = render_to_string('gestion/includes/form_cita_modal.html', {'form': form, 'paciente': paciente},
                                 request=request)
    return JsonResponse({'html_form': html_form})


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

    Cita.objects.create(paciente=paciente, tratamiento=tratamiento, fecha=fecha, hora=hora, motivo=motivo)
    return redirect('calendario')


@login_required
def completar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)

    # Si la cita estaba pendiente y ahora se marca como completada
    if not cita.completada:
        cita.completada = True
        cita.save()

        # Descontar del inventario
        if cita.tratamiento:
            materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento)
            for item in materiales:
                producto = item.producto
                if producto.cantidad_actual >= item.cantidad_usada:
                    producto.cantidad_actual -= item.cantidad_usada
                    producto.save()
                    messages.success(request, f"Se descontó {item.cantidad_usada} de {producto.nombre}.")
                else:
                    messages.warning(request, f"Stock insuficiente de {producto.nombre}.")
    else:
        # Si por error el usuario la vuelve a marcar como "Pendiente"
        cita.completada = False
        cita.save()

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def finalizar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if not cita.completada:
        cita.completada = True
        cita.save()
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
def completar_cita_con_pago(request, cita_id):
    if request.method == "POST":
        data = json.loads(request.body)
        cita = get_object_or_404(Cita, id=cita_id)

        if not cita.completada:
            cita.completada = True
            cita.save()

            # Descontar del inventario silenciosamente (sin messages porque es AJAX)
            if cita.tratamiento:
                materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento)
                for item in materiales:
                    producto = item.producto
                    if producto.cantidad_actual >= item.cantidad_usada:
                        producto.cantidad_actual -= item.cantidad_usada
                        producto.save()

        # Procesar el pago
        monto = data.get('monto')
        if monto and float(monto) > 0:
            Pago.objects.create(
                paciente=cita.paciente,
                monto=monto,
                notas=f"Pago por cita: {cita.tratamiento.nombre if cita.tratamiento else 'Consulta'}"
            )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


# ==========================================
# 5. MÓDULO DE TRATAMIENTOS Y MATERIALES
# ==========================================

@login_required
def lista_tratamientos(request):
    tratamientos = Tratamiento.objects.prefetch_related('materiales__producto').all().order_by('nombre')
    productos = Producto.objects.all().order_by('nombre')
    return render(request, 'gestion/lista_tratamientos.html', {'tratamientos': tratamientos, 'productos': productos})


@login_required
@grupo_requerido('Doctor') # <--- PROTEGIDO
def gestionar_tratamiento(request, pk=None):
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


@login_required
@grupo_requerido('Doctor')
@require_POST
def guardar_tratamiento(request):
    tratamiento_id = request.POST.get('tratamiento_id')
    nombre = request.POST.get('nombre')
    descripcion = request.POST.get('descripcion', '')
    costo_base = request.POST.get('costo_base', 0)

    if tratamiento_id:
        tratamiento = get_object_or_404(Tratamiento, pk=tratamiento_id)
        tratamiento.nombre = nombre
        tratamiento.descripcion = descripcion
        tratamiento.costo_base = costo_base
        tratamiento.save()
        MaterialTratamiento.objects.filter(tratamiento=tratamiento).delete()
    else:
        tratamiento = Tratamiento.objects.create(nombre=nombre, descripcion=descripcion, costo_base=costo_base)

    # ¡AQUÍ ESTÁ LA MAGIA! Sin corchetes []
    productos_ids = request.POST.getlist('producto_id')
    cantidades = request.POST.getlist('cantidad')

    for p_id, cant in zip(productos_ids, cantidades):
        if p_id and cant and int(cant) > 0:
            producto = get_object_or_404(Producto, pk=p_id)
            MaterialTratamiento.objects.create(tratamiento=tratamiento, producto=producto, cantidad_usada=int(cant))

    return redirect('lista_tratamientos')


# ==========================================
# 6. MÓDULO DE INVENTARIO
# ==========================================

@login_required
def inventario(request):
    productos = Producto.objects.all().order_by('nombre')
    total_productos = productos.count()
    productos_bajos = productos.filter(cantidad_actual__lte=F('stock_minimo')).count()
    valor_inventario = sum(p.cantidad_actual * p.precio_compra for p in productos)

    context = {
        'productos': productos,
        'total_productos': total_productos,
        'productos_bajos': productos_bajos,
        'valor_inventario': valor_inventario,
        'alertas': productos_bajos > 0,
    }
    return render(request, 'gestion/inventario.html', context)


@login_required
@grupo_requerido('Doctor') # <--- PROTEGIDO (Solo el admin crea nuevos productos)
@require_POST
def crear_producto(request):
    Producto.objects.create(
        nombre=request.POST.get('nombre'),
        descripcion=request.POST.get('descripcion', ''),
        cantidad_actual=request.POST.get('cantidad_actual', 0),
        stock_minimo=request.POST.get('stock_minimo', 5),
        precio_compra=request.POST.get('precio_compra', 0.00)
    )
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


# ==========================================
# 7. MÓDULO DE FINANZAS Y PAGOS
# ==========================================

@login_required
@grupo_requerido('Doctor') # <--- PROTEGIDO (Finanzas globales)
def reporte_finanzas(request):
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    pagos = Pago.objects.all()
    citas = Cita.objects.all()

    if fecha_inicio_str and fecha_fin_str:
        try:
            f_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
            f_fin = datetime.combine(datetime.strptime(fecha_fin_str, '%Y-%m-%d'), time.max)
            pagos = pagos.filter(fecha__range=(f_inicio, f_fin))
            citas = citas.filter(fecha__range=(f_inicio, f_fin))
        except ValueError:
            pass

    ingresos_totales = pagos.aggregate(total=Sum('monto'))['total'] or 0
    total_cargos = citas.aggregate(total=Sum('tratamiento__costo_base'))['total'] or 0
    deuda_total = total_cargos - ingresos_totales

    context = {
        'ingresos_totales': ingresos_totales,
        'deuda_total': deuda_total,
        'ultimos_pagos': pagos.select_related('paciente').order_by('-fecha'),
        'total_cargos': total_cargos,
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
    }
    return render(request, 'gestion/finanzas.html', context)


@login_required
def registrar_pago(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == "POST":
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                form = PagoForm(data)
                if form.is_valid():
                    pago = form.save(commit=False)
                    pago.paciente = paciente
                    pago.save()
                    return JsonResponse({'status': 'ok'})
                else:
                    return JsonResponse({'status': 'error', 'errores': form.errors})
            except Exception as e:
                return JsonResponse({'status': 'error', 'mensaje': str(e)})
        else:
            form = PagoForm(request.POST)
            if form.is_valid():
                pago = form.save(commit=False)
                pago.paciente = paciente
                pago.save()
                return redirect('detalle_paciente', pk=paciente.pk)
    else:
        form = PagoForm()

    return render(request, 'gestion/pago_form.html', {'form': form, 'paciente': paciente})