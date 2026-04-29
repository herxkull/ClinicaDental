from . import google_calendar
import json
import logging
from datetime import date, datetime, time
from decimal import Decimal
import openpyxl
from .utils import render_to_pdf
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, connection
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count, F, OuterRef, Subquery, DecimalField
from django.db.models.functions import Coalesce
from .decorators import grupo_requerido
from .models import Paciente, Cita, Tratamiento, Pago, ArchivoPaciente, Receta, Producto, MaterialTratamiento, GoogleCalendarConfig, ConfiguracionClinica
from .forms import PacienteForm, CitaForm, TratamientoForm, PagoForm, ArchivoPacienteForm, RecetaForm, ConfiguracionClinicaForm

# Inicializar Logger de AuditorÃ­a
audit_log = logging.getLogger('gestion.audit')

def log_audit(request, action, details=""):
    """Helper para registrar acciones con contexto de Tenant y Usuario"""
    tenant_name = getattr(request, 'tenant', 'N/A')
    user_id = request.user.username if request.user.is_authenticated else 'Anonymous'
    audit_log.info(f"ACTION: {action} | DETAILS: {details}", extra={
        'tenant_name': tenant_name,
        'user_id': user_id
    })

# 1. DASHBOARD PRINCIPAL
# ==========================================

@login_required
def dashboard(request):
    hoy = timezone.localtime(timezone.now()).date()
    total_pacientes = Paciente.objects.count()
    
    # --- PRÓXIMAS CITAS (Elegante y compacto) ---
    citas_proximas = Cita.objects.select_related('paciente', 'tratamiento').filter(
        fecha__gte=hoy, completada=False
    ).order_by('fecha', 'hora')[:5]

    # --- ALERTAS DE STOCK CRÍTICO ---
    productos_criticos = Producto.objects.filter(cantidad_actual__lte=F('stock_minimo')).order_by('cantidad_actual')
    alertas_inventario = productos_criticos.count()

    # --- KPIs FINANCIEROS Y TENDENCIAS ---
    primer_dia_mes = hoy.replace(day=1)
    ultimo_dia_mes_pasado = primer_dia_mes - timezone.timedelta(days=1)
    primer_dia_mes_pasado = ultimo_dia_mes_pasado.replace(day=1)

    # Ingresos
    ingresos_totales = Pago.objects.aggregate(total=Sum('monto'))['total'] or 0
    ingresos_mes_actual = Pago.objects.filter(fecha__date__gte=primer_dia_mes).aggregate(total=Sum('monto'))['total'] or 0
    ingresos_mes_pasado = Pago.objects.filter(
        fecha__date__gte=primer_dia_mes_pasado, 
        fecha__date__lte=ultimo_dia_mes_pasado
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    tendencia_ingresos = ((ingresos_mes_actual - ingresos_mes_pasado) / ingresos_mes_pasado * 100) if ingresos_mes_pasado > 0 else 0

    # --- DATOS PARA GRÁFICOS (APEXCHARTS) ---
    # 1. Top Tratamientos
    datos_tratamientos = Cita.objects.filter(fecha__gte=primer_dia_mes).values('tratamiento__nombre').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')[:5]
    
    chart_tratamientos_labels = [item['tratamiento__nombre'] or "Sin nombre" for item in datos_tratamientos]
    chart_tratamientos_series = [item['cantidad'] for item in datos_tratamientos]

    # 2. Ingresos vs Gastos (Últimos 6 meses)
    meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    chart_periodo_labels = []
    chart_ingresos_data = []
    chart_gastos_data = []

    for i in range(5, -1, -1):
        target_date = hoy - timezone.timedelta(days=i*30)
        m = target_date.month
        y = target_date.year
        chart_periodo_labels.append(f"{meses_nombres[m-1]}")
        
        ingreso = Pago.objects.filter(fecha__year=y, fecha__month=m).aggregate(total=Sum('monto'))['total'] or 0
        chart_ingresos_data.append(float(ingreso))
        
        # Gasto = materiales de citas completadas
        citas_mes = Cita.objects.filter(fecha__year=y, fecha__month=m, completada=True)
        gasto_total = 0
        for cita in citas_mes:
            if cita.tratamiento:
                gasto_total += float(cita.tratamiento.costo_materiales)
        chart_gastos_data.append(gasto_total)

    context = {
        'total_pacientes': total_pacientes,
        'citas_proximas': citas_proximas,
        'ingresos_totales': ingresos_totales,
        'ingresos_mes_actual': ingresos_mes_actual,
        'tendencia_ingresos': round(tendencia_ingresos, 1),
        'alertas_inventario': alertas_inventario,
        'productos_criticos': productos_criticos,
        'chart_tratamientos_labels': json.dumps(chart_tratamientos_labels),
        'chart_tratamientos_series': json.dumps(chart_tratamientos_series),
        'chart_periodo_labels': json.dumps(chart_periodo_labels),
        'chart_ingresos_data': json.dumps(chart_ingresos_data),
        'chart_gastos_data': json.dumps(chart_gastos_data),
        'pacientes_all': Paciente.objects.all().order_by('nombre'),
        'tratamientos_all': Tratamiento.objects.all().order_by('nombre'),
    }
    return render(request, 'gestion/dashboard.html', context)


# ==========================================
# 2. MÃ“DULO DE PACIENTES
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
    citas = Cita.objects.select_related('tratamiento').filter(paciente=paciente).order_by('-fecha')

    diccionario_dientes = paciente.odontograma_data if paciente.odontograma_data else {}

    total_tratamientos = 0
    for cita in citas:
        if cita.tratamiento and cita.tratamiento.precio_venta:
            total_tratamientos += cita.tratamiento.precio_venta

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

    headers = ['Nombre Completo', 'CÃ©dula', 'TelÃ©fono', 'Total Cargos', 'Total Pagado', 'Saldo Pendiente']
    ws.append(headers)

    # Subconsultas para evitar el problema N+1
    citas_sub = Cita.objects.filter(paciente=OuterRef('pk')).values('paciente').annotate(
        total=Sum('tratamiento__precio_venta')).values('total')

    pagos_sub = Pago.objects.filter(paciente=OuterRef('pk')).values('paciente').annotate(
        total=Sum('monto')).values('total')

    pacientes = Paciente.objects.annotate(
        total_cargos=Coalesce(Subquery(citas_sub), 0.0, output_field=DecimalField()),
        total_pagos=Coalesce(Subquery(pagos_sub), 0.0, output_field=DecimalField())
    ).order_by('nombre')

    for p in pacientes:
        saldo = p.total_cargos - p.total_pagos
        ws.append([p.nombre, p.cedula, p.telefono, p.total_cargos, p.total_pagos, saldo])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Pacientes_Hersan.xlsx"'
    wb.save(response)
    return response


@login_required
def estado_cuenta_pdf(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    cargos = Cita.objects.filter(paciente=paciente, completada=True).order_by('fecha')
    abonos = Pago.objects.filter(paciente=paciente).order_by('fecha')

    total_cargos = cargos.aggregate(total=Sum('tratamiento__precio_venta')).get('total') or 0
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
@grupo_requerido('Doctor') # <--- PROTEGIDO (SÃ³lo doctor escribe en el JSON masivo)
def api_odontograma(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            paciente.odontograma_data = data
            paciente.save()
            log_audit(request, "MODIFICACION_ODONTOGRAMA", f"Paciente: {paciente.nombre} (ID: {paciente.id})")
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    data = paciente.odontograma_data if paciente.odontograma_data else {}
    return JsonResponse(data)


@login_required
@grupo_requerido('Doctor') # <--- PROTEGIDO (ClÃ­nico)
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
@grupo_requerido('Doctor') # <--- PROTEGIDO (MÃ©dico)
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
# 4. MÃ“DULO DE CITAS Y CALENDARIO
# ==========================================

@login_required
def lista_citas(request):
    citas = Cita.objects.select_related('paciente', 'tratamiento').all().order_by('fecha', 'hora')
    return render(request, 'gestion/lista_citas.html', {'citas': citas})


@login_required
def calendario(request):
    pacientes = Paciente.objects.all().order_by('nombre')
    tratamientos = Tratamiento.objects.all().order_by('nombre')
    google_config = GoogleCalendarConfig.objects.filter(is_active=True).first()
    
    return render(request, 'gestion/calendario.html', {
        'pacientes': pacientes, 
        'tratamientos': tratamientos,
        'google_active': google_config is not None
    })


@login_required
def citas_json(request):
    citas = Cita.objects.select_related('paciente', 'tratamiento').all()
    eventos = []

    for cita in citas:
        start_dt = f"{cita.fecha.isoformat()}T{cita.hora.strftime('%H:%M:%S')}"
        nombre_tratamiento = cita.tratamiento.nombre if cita.tratamiento else "Consulta General"

        eventos.append({
            'id': cita.id,
            'title': f"{cita.paciente.nombre}",
            'start': start_dt,
            'url': reverse('detalle_paciente', args=[cita.paciente.pk]),
            'backgroundColor': cita.tratamiento.color if cita.tratamiento else '#3b82f6',
            'borderColor': cita.tratamiento.color if cita.tratamiento else '#3b82f6',
            'extendedProps': {
                'tratamiento_nombre': nombre_tratamiento,
                'motivo': cita.motivo,
                'paciente_nombre': cita.paciente.nombre
            }
        })

    return JsonResponse(eventos, safe=False)


@login_required
@require_POST
def reprogramar_cita(request):
    import json
    from datetime import datetime
    try:
        data = json.loads(request.body)
        cita = get_object_or_404(Cita, id=data.get('id'))
        
        # Parsear nueva fecha y hora (ISO string)
        new_start = data.get('start') # Ej: 2023-10-27T08:00:00
        dt_obj = datetime.fromisoformat(new_start.replace('Z', ''))
        
        cita.fecha = dt_obj.date()
        cita.hora = dt_obj.time()
        cita.save()
        
        # SincronizaciÃ³n automÃ¡tica con Google
        try:
            google_calendar.sync_cita_to_google(cita)
        except Exception as ge:
            print(f"Error Google Sync: {ge}")
        
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


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
    try:
        paciente = get_object_or_404(Paciente, id=paciente_id)

        if request.method == "POST":
            data = request.POST.copy()
            if not data.get('motivo'):
                data['motivo'] = "Consulta programada"

            form = CitaForm(data)

            if 'paciente' in form.errors:
                del form.errors['paciente']
            
            if form.is_valid():
                cita = form.save(commit=False)
                cita.paciente = paciente
                if not cita.motivo:
                    cita.motivo = "Consulta programada"
                cita.save()
                
                # SincronizaciÃ³n automÃ¡tica
                try:
                    google_calendar.sync_cita_to_google(cita)
                except Exception as ge:
                    print(f"Error Google Sync: {ge}")

                return JsonResponse({'status': 'ok'})

            html_form = render_to_string('gestion/includes/form_cita_modal.html', {'form': form, 'paciente': paciente},
                                         request=request)
            return JsonResponse({'status': 'error', 'html_form': html_form})

        form = CitaForm(initial={'paciente': paciente})
        html_form = render_to_string('gestion/includes/form_cita_modal.html', {'form': form, 'paciente': paciente},
                                     request=request)
        return JsonResponse({'html_form': html_form})
    except Exception as e:
        import traceback
        print("ERROR EN MODAL_NUEVA_CITA:", str(e))
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


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

    if not cita.completada:
        with transaction.atomic():
            cita.completada = True
            cita.save()

            if cita.tratamiento:
                materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento).select_related('producto')
                for item in materiales:
                    producto = item.producto
                    if producto.cantidad_actual >= item.cantidad_usada:
                        producto.cantidad_actual -= item.cantidad_usada
                        producto.save()
                        messages.success(request, f"Insumo utilizado: {item.cantidad_usada}x {producto.nombre}.")
                    else:
                        raise Exception(f"Stock insuficiente de {producto.nombre}.")
    else:
        with transaction.atomic():
            cita.completada = False
            cita.save()
            if cita.tratamiento:
                materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento).select_related('producto')
                for item in materiales:
                    producto = item.producto
                    producto.cantidad_actual += item.cantidad_usada
                    producto.save()

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def finalizar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if not cita.completada:
        with transaction.atomic():
            cita.completada = True
            cita.save()
            materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento).select_related('producto')
            for item in materiales:
                producto = item.producto
                if producto.cantidad_actual >= item.cantidad_usada:
                    producto.cantidad_actual -= item.cantidad_usada
                    producto.save()
                else:
                    raise Exception(f"Stock insuficiente de {producto.nombre}.")
    return redirect('dashboard')


@login_required
def completar_cita_con_pago(request, cita_id):
    if request.method == "POST":
        data = json.loads(request.body)
        cita = get_object_or_404(Cita, id=cita_id)

        with transaction.atomic():
            if not cita.completada:
                cita.completada = True
                cita.save()

                # Descontar del inventario
                if cita.tratamiento:
                    materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento).select_related('producto')
                    for item in materiales:
                        producto = item.producto
                        if producto.cantidad_actual >= item.cantidad_usada:
                            producto.cantidad_actual -= item.cantidad_usada
                            producto.save()
                        else:
                            raise Exception(f"Stock insuficiente de {producto.nombre}.")
            
            # Sincronizar estado con Google
            try:
                google_calendar.sync_cita_to_google(cita)
            except:
                pass

            # Procesar el pago
            monto = data.get('monto')
            metodo = data.get('metodo', 'EFECTIVO')
            if monto and float(monto) > 0:
                Pago.objects.create(
                    paciente=cita.paciente,
                    monto=monto,
                    metodo=metodo,
                    notas=f"Pago por cita: {cita.tratamiento.nombre if cita.tratamiento else 'Consulta'}"
                )
                log_audit(request, "FINALIZAR_CITA_COBRO", f"Paciente: {cita.paciente.nombre} | Monto: {monto}")
            
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


# ==========================================
# 5. MÃ“DULO DE TRATAMIENTOS Y MATERIALES
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
    precio_venta = request.POST.get('precio_venta', 0)

    if tratamiento_id:
        tratamiento = get_object_or_404(Tratamiento, pk=tratamiento_id)
        tratamiento.nombre = nombre
        tratamiento.descripcion = descripcion
        tratamiento.precio_venta = precio_venta
        tratamiento.save()
        MaterialTratamiento.objects.filter(tratamiento=tratamiento).delete()
    else:
        tratamiento = Tratamiento.objects.create(nombre=nombre, descripcion=descripcion, precio_venta=precio_venta)

    # Â¡AQUÃ ESTÃ LA MAGIA! Sin corchetes []
    productos_ids = request.POST.getlist('producto_id')
    cantidades = request.POST.getlist('cantidad')

    for p_id, cant in zip(productos_ids, cantidades):
        if p_id and cant and int(cant) > 0:
            producto = get_object_or_404(Producto, pk=p_id)
            MaterialTratamiento.objects.create(tratamiento=tratamiento, producto=producto, cantidad_usada=int(cant))

    return redirect('lista_tratamientos')


# ==========================================
# 6. MÃ“DULO DE INVENTARIO
# ==========================================

@login_required
def inventario(request):
    productos = Producto.objects.all().order_by('nombre')
    total_productos = productos.count()
    productos_bajos = productos.filter(cantidad_actual__lte=F('stock_minimo')).count()
    valor_inventario = productos.aggregate(
        total=Sum(F('cantidad_actual') * F('costo_unitario'))
    )['total'] or 0

    # KPI 2: Presupuesto de ReposiciÃ³n (Llevar productos en alerta a su stock_minimo)
    presupuesto_reposicion = productos.filter(cantidad_actual__lt=F('stock_minimo')).aggregate(
        total=Sum((F('stock_minimo') - F('cantidad_actual')) * F('costo_unitario'))
    )['total'] or 0

    # KPI 3: Inteligencia de Negocio (Ley de Pareto - Productos Top 80% InversiÃ³n)
    # Ordenamos por valor total invertido
    productos_ordenados = sorted(productos, key=lambda p: p.total_valor_stock, reverse=True)
    inversion_acumulada = 0
    productos_top_ids = []
    
    for p in productos_ordenados:
        inversion_acumulada += p.total_valor_stock
        productos_top_ids.append(p.id)
        if valor_inventario > 0 and inversion_acumulada >= (valor_inventario * Decimal('0.8')):
            break
    
    # Marcamos los 3 primeros siempre o hasta cubrir el 80%
    productos_top_ids = productos_top_ids[:3]

    context = {
        'productos': productos,
        'total_productos': total_productos,
        'productos_bajos': productos_bajos,
        'valor_inventario': valor_inventario,
        'presupuesto_reposicion': presupuesto_reposicion,
        'productos_top_ids': productos_top_ids,
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
        costo_unitario=request.POST.get('costo_unitario', 0.00),
        precio_venta_sugerido=request.POST.get('precio_venta_sugerido', 0.00)
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
# 7. MÃ“DULO DE FINANZAS Y PAGOS
# ==========================================

@login_required
@grupo_requerido('Doctor')
def reporte_finanzas(request):
    hoy = timezone.localtime(timezone.now()).date()
    primer_dia_mes = hoy.replace(day=1)
    
    # 1. FILTROS DINÃMICOS
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    metodo_pago = request.GET.get('metodo')
    estado_pago = request.GET.get('estado') # 'pagado', 'pendiente'
    search_query = request.GET.get('q')

    pagos = Pago.objects.select_related('paciente', 'cita__tratamiento')
    citas = Cita.objects.select_related('paciente', 'tratamiento')

    if fecha_inicio_str and fecha_fin_str:
        try:
            f_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            f_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            pagos = pagos.filter(fecha__date__range=(f_inicio, f_fin))
            citas = citas.filter(fecha__range=(f_inicio, f_fin))
        except ValueError:
            pass

    if metodo_pago:
        pagos = pagos.filter(metodo=metodo_pago)

    if search_query:
        pagos = pagos.filter(Q(paciente__nombre__icontains=search_query) | Q(notas__icontains=search_query))
        citas = citas.filter(paciente__nombre__icontains=search_query)

    # 2. MÃ‰TRICAS PRINCIPALES (KPIs)
    ingresos_totales = pagos.aggregate(total=Sum('monto'))['total'] or 0
    total_facturado = citas.aggregate(total=Sum('tratamiento__precio_venta'))['total'] or 0
    deuda_total = total_facturado - ingresos_totales

    # Tendencia (vs Mes Anterior)
    ultimo_dia_mes_pasado = primer_dia_mes - timezone.timedelta(days=1)
    primer_dia_mes_pasado = ultimo_dia_mes_pasado.replace(day=1)
    
    ingresos_mes_pasado = Pago.objects.filter(
        fecha__date__range=(primer_dia_mes_pasado, ultimo_dia_mes_pasado)
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    tendencia_ingresos = ((ingresos_totales - ingresos_mes_pasado) / ingresos_mes_pasado * 100) if ingresos_mes_pasado > 0 else 100

    # Punto de Equilibrio
    gastos_fijos = getattr(request.tenant, 'gastos_fijos', 0)
    falta_punto_equilibrio = max(0, gastos_fijos - ingresos_totales)
    progreso_equilibrio = min(100, (ingresos_totales / gastos_fijos * 100)) if gastos_fijos > 0 else 100

    # 3. DATOS PARA GRÃFICOS (Data Viz)
    # Columna A: Flujo 30 dÃ­as
    hace_30_dias = hoy - timezone.timedelta(days=30)
    flujo_30_dias = Pago.objects.filter(fecha__date__gte=hace_30_dias).extra(
        select={'day': "date(fecha)"}
    ).values('day').annotate(total=Sum('monto')).order_by('day')
    
    labels_flujo = [item['day'].strftime('%d %b') if isinstance(item['day'], date) else item['day'] for item in flujo_30_dias]
    data_flujo = [float(item['total']) for item in flujo_30_dias]

    # Columna B: Ingresos por Tratamiento
    ingresos_por_tratamiento = Pago.objects.filter(cita__isnull=False).values(
        'cita__tratamiento__nombre'
    ).annotate(total=Sum('monto')).order_by('-total')[:5]
    
    labels_tratamientos = [item['cita__tratamiento__nombre'] for item in ingresos_por_tratamiento]
    data_tratamientos = [float(item['total']) for item in ingresos_por_tratamiento]

    # 4. TABLA DE MOVIMIENTOS PRO (Aging & Status)
    movimientos = []
    # AÃ±adimos pagos realizados
    for p in pagos.order_by('-fecha')[:50]:
        movimientos.append({
            'tipo': 'INGRESO',
            'fecha': p.fecha,
            'paciente': p.paciente,
            'concepto': p.notas or (p.cita.tratamiento.nombre if p.cita else "Pago General"),
            'monto': p.monto,
            'metodo': p.get_metodo_display(),
            'estado': 'COMPLETO',
            'es_mora': False
        })
    
    # AÃ±adimos citas pendientes de pago (Aging > 15 dÃ­as)
    limite_mora = hoy - timezone.timedelta(days=15)
    citas_pendientes = citas.filter(completada=True, fecha__lte=limite_mora).annotate(
        pagado=Coalesce(Sum('pagos_detalle__monto'), 0, output_field=DecimalField())
    ).filter(pagado__lt=F('tratamiento__precio_venta'))

    for c in citas_pendientes:
        movimientos.append({
            'tipo': 'DEUDA',
            'fecha': datetime.combine(c.fecha, time.min),
            'paciente': c.paciente,
            'concepto': f"Pendiente: {c.tratamiento.nombre}",
            'monto': c.tratamiento.precio_venta - c.pagado,
            'metodo': 'N/A',
            'estado': 'PENDIENTE',
            'es_mora': True
        })

    # Ordenar por fecha descendente
    movimientos.sort(key=lambda x: x['fecha'], reverse=True)

    context = {
        'ingresos_totales': ingresos_totales,
        'total_facturado': total_facturado,
        'deuda_total': deuda_total,
        'tendencia_ingresos': round(tendencia_ingresos, 1),
        'gastos_fijos': gastos_fijos,
        'falta_equilibrio': falta_punto_equilibrio,
        'progreso_equilibrio': round(progreso_equilibrio, 1),
        'labels_flujo': json.dumps(labels_flujo),
        'data_flujo': json.dumps(data_flujo),
        'labels_tratamientos': json.dumps(labels_tratamientos),
        'data_tratamientos': json.dumps(data_tratamientos),
        'movimientos': movimientos,
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
        'search_query': search_query,
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
                    log_audit(request, "REGISTRO_PAGO", f"Paciente: {paciente.nombre} | Monto: {pago.monto}")
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
                log_audit(request, "REGISTRO_PAGO", f"Paciente: {paciente.nombre} | Monto: {pago.monto}")
                return redirect('detalle_paciente', pk=paciente.pk)
    else:
        form = PagoForm()

    return render(request, 'gestion/pago_form.html', {'form': form, 'paciente': paciente})


# ==========================================
# 7. INTEGRACIÃ“N GOOGLE CALENDAR (OAuth2)
# ==========================================

from google_auth_oauthlib.flow import Flow
from django.conf import settings

@login_required
@grupo_requerido('Doctor')
def google_calendar_init(request):
    """Inicia el flujo de autenticaciÃ³n con Google"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly']
    )
    
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    request.session['google_auth_state'] = state
    return redirect(authorization_url)


@login_required
@grupo_requerido('Doctor')
def google_calendar_callback(request):
    """Callback de Google para guardar las credenciales"""
    state = request.session.get('google_auth_state')
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly'],
        state=state
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    # Obtener el token
    authorization_response = request.build_absolute_uri()
    if not settings.DEBUG and 'http://' in authorization_response:
        authorization_response = authorization_response.replace('http://', 'https://')
        
    flow.fetch_token(authorization_response=authorization_response)
    
    credentials = flow.credentials
    
    # Guardar en la base de datos del Tenant
    config, created = GoogleCalendarConfig.objects.get_or_create(id=1)
    config.credentials_json = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    config.is_active = True
    config.save()
    
    return redirect('calendario')
@login_required
@grupo_requerido('Doctor')
def panel_configuracion(request):
    config, created = ConfiguracionClinica.objects.get_or_create(id=1)
    google_config = GoogleCalendarConfig.objects.filter(id=1).first()

    if request.method == 'POST':
        form = ConfiguracionClinicaForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            horarios = {}
            dias = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
            for dia in dias:
                apertura = request.POST.get(f'apertura_{dia}')
                cierre = request.POST.get(f'cierre_{dia}')
                if apertura and cierre:
                    horarios[dia] = [apertura, cierre]
            config.horarios_atencion = horarios
            config.save()
            messages.success(request, '¡Configuración actualizada con éxito!')
            return redirect('panel_configuracion')
    else:
        form = ConfiguracionClinicaForm(instance=config)

    context = {
        'form': form,
        'config': config,
        'google_config': google_config,
        'dias': ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    }
    return render(request, 'gestion/configuraciones.html', context)

