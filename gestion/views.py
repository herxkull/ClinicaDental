from . import google_calendar
import json
import logging
import os
import secrets
import uuid
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
import decimal
import openpyxl
from .utils import render_to_pdf
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.models import User
from django.core.signing import TimestampSigner, SignatureExpired
from django.contrib.auth.decorators import login_required
from django.db import transaction, connection
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string

def magic_login(request):
    token = request.GET.get('token')
    if not token:
        return HttpResponse("Token faltante", status=400)
    
    signer = TimestampSigner()
    try:
        # El token expira en 10 minutos
        username = signer.unsign(token, max_age=600)
        user = User.objects.get(username=username)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect('dashboard')
    except (SignatureExpired, User.DoesNotExist, Exception) as e:
        return HttpResponse(f"Token invÃ¡lido o expirado: {e}", status=403)
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count, F, OuterRef, Subquery, DecimalField
from django.db.models.functions import Coalesce
from .decorators import grupo_requerido
from .models import Paciente, Cita, Tratamiento, Pago, ArchivoPaciente, Receta, Producto, MaterialTratamiento, GoogleCalendarConfig, ConfiguracionClinica, MovimientoInventario, DoctorColaborador, LogActividad
from .forms import PacienteForm, CitaForm, TratamientoForm, PagoForm, ArchivoPacienteForm, RecetaForm, ConfiguracionClinicaForm

# Inicializar Logger de Auditori­a
audit_log = logging.getLogger('gestion.audit')

def log_audit(request, action, details=""):
    """Helper para registrar acciones con contexto de Tenant y Usuario"""
    tenant_name = getattr(request, 'tenant', 'N/A')
    user = request.user if request.user.is_authenticated else None
    user_id = user.username if user else 'Anonymous'
    
    # 1. Log a archivo (Logging standard)
    audit_log.info(f"ACTION: {action} | DETAILS: {details}", extra={
        'tenant_name': tenant_name,
        'user_id': user_id
    })

    # 2. Log a Base de Datos (Auditoría visible en UI)
    try:
        LogActividad.objects.create(
            usuario=user,
            accion=action,
            detalles=details,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    except Exception as e:
        print(f"Error al guardar log de auditoría: {e}")

# 1. DASHBOARD PRINCIPAL
# ==========================================

@login_required
def dashboard(request):
    hoy = timezone.localtime(timezone.now()).date()
    total_pacientes = Paciente.objects.count()
    
    # --- PRÓXIMAS CITAS (Elegante y compacto) ---
    citas_proximas = Cita.objects.select_related('paciente', 'tratamiento', 'doctor').filter(
        fecha=hoy
    ).order_by('hora')[:5]

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

    # 2. Ingresos vs Gastos (Últimos 6 meses - Optimizado con Agregaciones)
    meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    chart_periodo_labels = []
    chart_ingresos_data = []
    chart_gastos_data = []

    # Obtener ingresos agrupados por mes de los últimos 6 meses
    seis_meses_atras = primer_dia_mes - timezone.timedelta(days=150)
    ingresos_qs = Pago.objects.filter(fecha__date__gte=seis_meses_atras).annotate(
        mes=F('fecha__month'),
        anio=F('fecha__year')
    ).values('mes', 'anio').annotate(total=Sum('monto')).order_by('anio', 'mes')

    # Obtener gastos (materiales) agrupados por mes
    gastos_qs = Cita.objects.filter(fecha__gte=seis_meses_atras, estado='COMPLETADA').annotate(
        mes=F('fecha__month'),
        anio=F('fecha__year')
    ).values('mes', 'anio').annotate(
        total_gasto=Sum(Coalesce('tratamiento__materiales', Decimal('0'), output_field=DecimalField()))
    ).order_by('anio', 'mes')

    # Mapear datos para fácil acceso
    ingresos_map = {(d['mes'], d['anio']): float(d['total']) for d in ingresos_qs}
    gastos_map = {(d['mes'], d['anio']): float(d['total_gasto']) for d in gastos_qs}

    mes_actual = hoy.month
    anio_actual = hoy.year

    for i in range(5, -1, -1):
        m = mes_actual - i
        y = anio_actual
        if m <= 0:
            m += 12
            y -= 1
        chart_periodo_labels.append(meses_nombres[m-1])
        chart_ingresos_data.append(ingresos_map.get((m, y), 0.0))
        chart_gastos_data.append(gastos_map.get((m, y), 0.0))

    # --- CUENTAS POR COBRAR (Acción Rápida) ---
    pacientes_con_saldo = []
    for p in Paciente.objects.all():
        citas_p = Cita.objects.filter(paciente=p)
        total_trat = sum(float(c.tratamiento.precio_venta or 0) for c in citas_p if c.tratamiento)
        total_pagos_p = float(Pago.objects.filter(paciente=p).aggregate(total=Sum('monto'))['total'] or 0)
        saldo_p = total_trat - total_pagos_p
        if saldo_p > 0:
            ultima_cita = citas_p.order_by('-fecha').first()
            fecha_ultimo = ultima_cita.fecha if ultima_cita else None
            pacientes_con_saldo.append({
                'paciente': p,
                'saldo': saldo_p,
                'fecha_ultimo': fecha_ultimo
            })
    pacientes_con_saldo.sort(key=lambda x: x['saldo'], reverse=True)
    cuentas_por_cobrar = pacientes_con_saldo[:5]

    context = {
        'cuentas_por_cobrar': cuentas_por_cobrar,
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
        'doctores_all': DoctorColaborador.objects.filter(is_active=True).order_by('nombre'),
    }
    return render(request, 'gestion/dashboard.html', context)


@login_required
def api_dashboard_stats(request):
    periodo = request.GET.get('periodo', 'mes')
    hoy = timezone.localtime(timezone.now()).date()
    
    if periodo == 'hoy':
        start_date = hoy
    elif periodo == 'semana':
        start_date = hoy - timezone.timedelta(days=hoy.weekday())
    else: # mes
        start_date = hoy.replace(day=1)

    # Filtrado de Datos
    ingresos = Pago.objects.filter(fecha__date__gte=start_date).aggregate(total=Sum('monto'))['total'] or 0
    pacientes_nuevos = Paciente.objects.filter(id__gt=0).count() # Placeholder
    
    # Top Tratamientos (Ingresos) para el periodo
    datos_tratamientos = Pago.objects.filter(fecha__date__gte=start_date).values(
        'cita__tratamiento__nombre'
    ).annotate(total=Sum('monto')).order_by('-total')[:5]
    
    labels = [item['cita__tratamiento__nombre'] or "Abonos/Otros" for item in datos_tratamientos]
    series = [float(item['total']) for item in datos_tratamientos]

    return JsonResponse({
        'ingresos': float(ingresos),
        'pacientes': pacientes_nuevos,
        'chart_labels': labels,
        'chart_series': series,
    })


# ==========================================
# 2. MÃ“DULO DE PACIENTES
# ==========================================

@login_required
def lista_pacientes(request):
    query = request.GET.get('q')
    solo_deudores = request.GET.get('con_deuda') == 'on'

    from django.db.models import Subquery, OuterRef, DecimalField
    from django.db.models.functions import Coalesce

    # Subconsultas para cálculo de saldo sin duplicar filas
    citas_sub = Cita.objects.filter(paciente=OuterRef('pk')).values('paciente').annotate(
        total=Sum('tratamiento__precio_venta')
    ).values('total')

    pagos_sub = Pago.objects.filter(paciente=OuterRef('pk')).values('paciente').annotate(
        total=Sum('monto')
    ).values('total')

    pacientes_lista = Paciente.objects.annotate(
        total_t=Coalesce(Subquery(citas_sub), 0, output_field=DecimalField()),
        total_p=Coalesce(Subquery(pagos_sub), 0, output_field=DecimalField())
    ).annotate(
        saldo=F('total_t') - F('total_p')
    ).order_by('nombre')

    if query:
        pacientes_lista = pacientes_lista.filter(
            Q(nombre__icontains=query) | Q(cedula__icontains=query)
        )

    if solo_deudores:
        pacientes_lista = pacientes_lista.filter(saldo__gt=0)

    paginator = Paginator(pacientes_lista, 10)
    page_number = request.GET.get('page')
    pacientes = paginator.get_page(page_number)

    return render(request, 'gestion/lista_pacientes.html', {
        'pacientes': pacientes, 
        'query': query,
        'solo_deudores': solo_deudores
    })


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
    """Maneja la subida de archivos con UUID para evitar colisiones"""
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        archivo = request.FILES.get('archivo')
        titulo = request.POST.get('titulo')
        
        if archivo:
            # Generar nombre único
            ext = archivo.name.split('.')[-1]
            archivo.name = f"{uuid.uuid4()}.{ext}"
            
            ArchivoPaciente.objects.create(
                paciente=paciente,
                titulo=titulo or "Archivo sin título",
                archivo=archivo
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            return redirect('detalle_paciente', pk=paciente.pk)
            
    return redirect('detalle_paciente', pk=paciente.pk)

@login_required
def editar_paciente_rapido(request, pk):
    """Vista para el modal de edición rápida"""
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        paciente.nombre = request.POST.get('nombre')
        paciente.telefono = request.POST.get('telefono')
        paciente.email = request.POST.get('email')
        paciente.alergias = request.POST.get('alergias')
        paciente.diabetes = 'diabetes' in request.POST
        paciente.hipertension = 'hipertension' in request.POST
        paciente.save()
        return JsonResponse({'status': 'success'})
    
    return render(request, 'gestion/modals/editar_paciente.html', {'paciente': paciente})


@login_required
@grupo_requerido('Doctor', 'Recepcionista') # <--- PROTEGIDO
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
    cargos = Cita.objects.filter(paciente=paciente, estado='COMPLETADA').order_by('fecha')
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
@grupo_requerido('Doctor', 'Recepcionista')
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
@grupo_requerido('Doctor', 'Recepcionista')
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
    doctores = DoctorColaborador.objects.filter(is_active=True).order_by('nombre')
    google_config = GoogleCalendarConfig.objects.filter(is_active=True).first()
    
    return render(request, 'gestion/calendario.html', {
        'pacientes': pacientes, 
        'tratamientos': tratamientos,
        'doctores': doctores,
        'google_active': google_config is not None
    })


@login_required
def citas_json(request):
    # 1. Citas locales (DentalSaaS)
    doctor_id = request.GET.get('doctor_id', 'all')
    citas = Cita.objects.select_related('paciente', 'tratamiento', 'doctor').all()
    
    if doctor_id != 'all':
        citas = citas.filter(doctor_id=doctor_id)
    eventos = []

    for cita in citas:
        start_dt = f"{cita.fecha.isoformat()}T{cita.hora.strftime('%H:%M:%S')}"
        nombre_tratamiento = cita.tratamiento.nombre if cita.tratamiento else "Consulta General"

        color = '#3b82f6'
        if cita.doctor and cita.doctor.color_agenda:
            color = cita.doctor.color_agenda
        elif cita.tratamiento and cita.tratamiento.color:
            color = cita.tratamiento.color

        eventos.append({
            'id': f"local_{cita.id}",
            'title': f"{cita.paciente.nombre}",
            'start': start_dt,
            'url': reverse('detalle_paciente', args=[cita.paciente.pk]),
            'backgroundColor': color,
            'borderColor': color,
            'color': color,
            'extendedProps': {
                'tratamiento_nombre': nombre_tratamiento,
                'motivo': cita.motivo,
                'paciente_nombre': cita.paciente.nombre
            }
        })

    # 2. Eventos externos (Google Calendar)
    google_config = GoogleCalendarConfig.objects.filter(is_active=True).first()
    if google_config:
        try:
            g_events = google_calendar.fetch_google_events(google_config)
            for g_event in g_events:
                # Evitar duplicados (no mostrar eventos que nosotros mismos enviamos a Google)
                g_id = g_event.get('id')
                if Cita.objects.filter(google_event_id=g_id).exists():
                    continue
                    
                start = g_event['start'].get('dateTime', g_event['start'].get('date'))
                end = g_event['end'].get('dateTime', g_event['end'].get('date'))
                
                eventos.append({
                    'id': f"google_{g_id}",
                    'title': f"[Google] {g_event.get('summary', '(Sin título)')}",
                    'start': start,
                    'end': end,
                    'backgroundColor': '#94a3b8', # Gris para eventos externos
                    'borderColor': '#94a3b8',
                    'editable': False, # No permitir mover eventos de Google desde aquí
                    'extendedProps': {
                        'tratamiento_nombre': 'Evento Externo',
                        'motivo': g_event.get('description', 'Evento sincronizado de Google Calendar'),
                        'paciente_nombre': 'Google User'
                    }
                })
        except Exception as ge_error:
            print(f"Error cargando eventos de Google Calendar: {ge_error}")

    return JsonResponse(eventos, safe=False)



@login_required
@require_POST
def reprogramar_cita(request):
    import json
    from datetime import datetime
    try:
        data = json.loads(request.body)
        raw_id = str(data.get('id'))
        # Limpiar el prefijo 'local_' si existe
        clean_id = raw_id.replace('local_', '')
        cita = get_object_or_404(Cita, id=clean_id)
        
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
            cita = form.save()
            try:
                google_calendar.sync_cita_to_google(cita)
            except Exception as ge:
                messages.error(request, f"Error sincronizando con Google Calendar: {ge}")
            return redirect('dashboard')
    else:
        form = CitaForm()
    return render(request, 'gestion/cita_form.html', {'form': form})


@login_required
def modal_nueva_cita(request, paciente_id):
    """Modal para agendar cita con selección de doctor"""
    paciente = get_object_or_404(Paciente, id=paciente_id)
    tratamientos = Tratamiento.objects.all()
    doctores = DoctorColaborador.objects.filter(is_active=True)
    
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.paciente = paciente
            # El doctor se asigna automáticamente vía el ModelForm o manualmente aquí
            cita.save()
            return JsonResponse({'status': 'success'})
        else:
            from django.template.loader import render_to_string
            html_form = render_to_string('gestion/modals/nueva_cita.html', {
                'paciente': paciente,
                'tratamientos': tratamientos,
                'doctores': doctores,
                'form': form
            }, request=request)
            return JsonResponse({'status': 'error', 'html_form': html_form}, status=400)

    from django.template.loader import render_to_string
    html_form = render_to_string('gestion/modals/nueva_cita.html', {
        'paciente': paciente,
        'tratamientos': tratamientos,
        'doctores': doctores
    }, request=request)
    
    return JsonResponse({'html_form': html_form})


@login_required
@require_POST
@grupo_requerido('Doctor', 'Recepcionista')
def guardar_cita_calendario(request):
    paciente_id = request.POST.get('paciente')
    tratamiento_id = request.POST.get('tratamiento')
    doctor_id = request.POST.get('doctor')
    fecha = request.POST.get('fecha')
    hora = request.POST.get('hora')
    motivo = request.POST.get('motivo')

    paciente = get_object_or_404(Paciente, pk=paciente_id)
    tratamiento = get_object_or_404(Tratamiento, pk=tratamiento_id) if tratamiento_id else None
    doctor = get_object_or_404(DoctorColaborador, pk=doctor_id) if doctor_id else None

    cita = Cita.objects.create(paciente=paciente, tratamiento=tratamiento, doctor=doctor, fecha=fecha, hora=hora, motivo=motivo)
    
    # Sincronización con Google
    try:
        google_calendar.sync_cita_to_google(cita)
    except Exception as ge:
        messages.error(request, f"Error sincronizando con Google Calendar: {ge}")

    # Recordatorio WhatsApp
    enviar_recordatorio_whatsapp(paciente, cita)
        
    return redirect('calendario')


@login_required
def completar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)

    if cita.estado != 'COMPLETADA':
        with transaction.atomic():
            cita.estado = 'COMPLETADA'
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
            cita.estado = 'PENDIENTE'
            cita.save()
            if cita.tratamiento:
                materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento).select_related('producto')
                for item in materiales:
                    producto = item.producto
                    producto.cantidad_actual += item.cantidad_usada
                    producto.save()

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def imprimir_ticket_pago(request, pago_id):
    pago = get_object_or_404(Pago.objects.select_related('paciente', 'cita__tratamiento'), id=pago_id)
    config = ConfiguracionClinica.objects.first()
    return render(request, 'gestion/ticket_pago.html', {
        'pago': pago,
        'config': config
    })

@login_required
def finalizar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if cita.estado != 'COMPLETADA':
        with transaction.atomic():
            cita.estado = 'COMPLETADA'
            cita.save()
            materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento).select_related('producto')
            for item in materiales:
                producto = item.producto
                if producto.cantidad_actual >= item.cantidad_usada:
                    producto.cantidad_actual -= item.cantidad_usada
                    producto.save()
                else:
                    raise Exception(f"Stock insuficiente de {producto.nombre}.")
            
            # Sincronización con Google
            try:
                google_calendar.sync_cita_to_google(cita)
            except Exception as ge:
                print(f"Error Google Sync: {ge}")
        
    return redirect('dashboard')


@login_required
@require_POST
def completar_cita_con_pago(request, cita_id):
    """
    Vista transaccional para finalizar una cita y registrar el pago.
    """
    try:
        data = json.loads(request.body)
        cita = get_object_or_404(Cita, id=cita_id)

        if cita.estado == 'COMPLETADA':
            return JsonResponse({'status': 'error', 'message': 'La cita ya está completada.'}, status=400)

        with transaction.atomic():
            # 1. Actualizar estado de la cita
            cita.estado = 'COMPLETADA'
            cita.save()

            # 2. Descontar del inventario (si hay insumos)
            if cita.tratamiento:
                materiales = MaterialTratamiento.objects.filter(tratamiento=cita.tratamiento).select_related('producto')
                for item in materiales:
                    producto = item.producto
                    if producto.cantidad_actual >= item.cantidad_usada:
                        producto.cantidad_actual -= item.cantidad_usada
                        producto.save()
                    else:
                        # Lanzamos excepción para que transaction.atomic haga rollback
                        raise Exception(f"Stock insuficiente de {producto.nombre}. (Disponible: {producto.cantidad_actual})")
            
            # 3. Registrar el pago
            monto = data.get('monto')
            monto_recibido = data.get('monto_recibido', 0)
            metodo = data.get('metodo', 'EFECTIVO')
            notas = data.get('notas', '')
            
            pago = None
            if monto and float(monto) >= 0:
                pago = Pago.objects.create(
                    paciente=cita.paciente,
                    cita=cita,
                    monto=monto,
                    monto_recibido=monto_recibido if monto_recibido else monto,
                    metodo=metodo,
                    notas=notas or f"Pago por cita: {cita.tratamiento.nombre if cita.tratamiento else 'Consulta'}"
                )
                log_audit(request, "FINALIZAR_CITA_COBRO", f"Paciente: {cita.paciente.nombre} | Monto: {monto}")

            # 4. Sincronizar con Google Calendar (Opcional, no bloqueante si falla fuera del atomic o manejado)
            try:
                google_calendar.sync_cita_to_google(cita)
            except Exception as e:
                print(f"Error sincronizando con Google: {e}")

        return JsonResponse({
            'status': 'ok', 
            'message': 'Cita finalizada y pago registrado correctamente.',
            'pago_id': pago.id if pago else None
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ==========================================
# 5. MÃ“DULO DE TRATAMIENTOS Y MATERIALES
# ==========================================

@login_required
def lista_tratamientos(request):
    tratamientos = Tratamiento.objects.prefetch_related('materiales__producto').all().order_by('nombre')
    productos = Producto.objects.all().order_by('nombre')
    doctores = DoctorColaborador.objects.all().order_by('nombre')
    return render(request, 'gestion/lista_tratamientos.html', {
        'tratamientos': tratamientos, 
        'productos': productos,
        'doctores': doctores
    })


@login_required
@grupo_requerido('Doctor', 'Recepcionista') # <--- PROTEGIDO
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
@require_POST
def guardar_tratamiento(request):
    tratamiento_id = request.POST.get('tratamiento_id')
    nombre = request.POST.get('nombre')
    descripcion = request.POST.get('descripcion', '')
    precio_venta = request.POST.get('precio_venta')
    comision = request.POST.get('comision_clinica_porcentaje', 30.00)
    doctor_id = request.POST.get('doctor_referencia')

    if tratamiento_id:
        tratamiento = get_object_or_404(Tratamiento, pk=tratamiento_id)
        tratamiento.nombre = nombre
        tratamiento.descripcion = descripcion
        tratamiento.precio_venta = precio_venta
        tratamiento.comision_clinica_porcentaje = comision
        if doctor_id:
            tratamiento.doctor_referencia_id = doctor_id
        tratamiento.save()
        MaterialTratamiento.objects.filter(tratamiento=tratamiento).delete()
    else:
        tratamiento = Tratamiento.objects.create(
            nombre=nombre, 
            descripcion=descripcion, 
            precio_venta=precio_venta,
            comision_clinica_porcentaje=comision,
            doctor_referencia_id=doctor_id if doctor_id else None
        )

    # Â¡AQUÃ  ESTÃ  LA MAGIA! Sin corchetes []
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
    # 1. Filtros y Búsqueda
    q = request.GET.get('q', '')
    cat = request.GET.get('cat', '')
    
    productos = Producto.objects.all().order_by('nombre')
    
    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(barcode__icontains=q))
    if cat:
        productos = productos.filter(categoria=cat)

    total_productos = productos.count()
    productos_bajos = productos.filter(cantidad_actual__lte=F('stock_minimo')).count()
    
    valor_inventario = productos.aggregate(
        total=Sum(F('cantidad_actual') * F('costo_unitario'))
    )['total'] or 0

    presupuesto_reposicion = productos.filter(cantidad_actual__lt=F('stock_minimo')).aggregate(
        total=Sum((F('stock_minimo') - F('cantidad_actual')) * F('costo_unitario'))
    )['total'] or 0

    context = {
        'productos': productos,
        'total_productos': total_productos,
        'productos_bajos': productos_bajos,
        'valor_inventario': valor_inventario,
        'presupuesto_reposicion': presupuesto_reposicion,
        'categorias': Producto.CATEGORIAS,
        'q': q,
        'cat_actual': cat,
    }
    return render(request, 'gestion/inventario.html', context)

@login_required
@grupo_requerido('Doctor', 'Recepcionista')
@require_POST
def registrar_movimiento(request):
    producto_id = request.POST.get('producto_id')
    tipo = request.POST.get('tipo') # ENTRADA, SALIDA, AJUSTE
    cantidad = int(request.POST.get('cantidad', 0))
    notas = request.POST.get('notas', '')
    nuevo_costo = request.POST.get('nuevo_costo')

    producto = get_object_or_404(Producto, pk=producto_id)
    
    with transaction.atomic():
        stock_anterior = producto.cantidad_actual
        
        if tipo == 'ENTRADA':
            producto.cantidad_actual += cantidad
            if nuevo_costo:
                producto.costo_unitario = Decimal(nuevo_costo)
        elif tipo == 'SALIDA':
            producto.cantidad_actual = max(0, producto.cantidad_actual - cantidad)
        elif tipo == 'AJUSTE':
            producto.cantidad_actual = cantidad # En ajuste, la cantidad enviada es el nuevo total
        
        producto.save()

        MovimientoInventario.objects.create(
            producto=producto,
            usuario=request.user,
            tipo=tipo,
            cantidad=cantidad if tipo != 'AJUSTE' else (producto.cantidad_actual - stock_anterior),
            stock_anterior=stock_anterior,
            stock_nuevo=producto.cantidad_actual,
            notas=notas
        )

    messages.success(request, f"Movimiento registrado para {producto.nombre}")
    return redirect('inventario')

@login_required
def historial_movimientos(request, producto_id=None):
    if producto_id:
        movimientos = MovimientoInventario.objects.filter(producto_id=producto_id)
        producto = get_object_or_404(Producto, pk=producto_id)
    else:
        movimientos = MovimientoInventario.objects.all()
        producto = None
    
    return render(request, 'gestion/historial_inventario.html', {
        'movimientos': movimientos[:100],
        'producto': producto
    })


@login_required
@grupo_requerido('Doctor', 'Recepcionista')
@require_POST
def crear_producto(request):
    Producto.objects.create(
        nombre=request.POST.get('nombre'),
        categoria=request.POST.get('categoria', 'OTROS'),
        barcode=request.POST.get('barcode', ''),
        descripcion=request.POST.get('descripcion', ''),
        cantidad_actual=request.POST.get('cantidad_actual', 0),
        stock_minimo=request.POST.get('stock_minimo', 5),
        costo_unitario=request.POST.get('costo_unitario', 0.00),
        precio_venta_sugerido=request.POST.get('precio_venta_sugerido', 0.00)
    )
    messages.success(request, "Producto creado exitosamente.")
    return redirect('inventario')


# ==========================================
# 7. MÃ“DULO DE FINANZAS Y PAGOS
# ==========================================

@login_required
@grupo_requerido('Doctor')
def reporte_finanzas(request):
    hoy = timezone.localtime(timezone.now()).date()
    primer_dia_mes = hoy.replace(day=1)
    
    # 1. FILTROS DINÃ MICOS
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    metodo_pago = request.GET.get('metodo')
    estado_pago = request.GET.get('estado') # 'pagado', 'pendiente'
    search_query = request.GET.get('q')

    pagos = Pago.objects.select_related('paciente', 'cita__tratamiento')
    citas = Cita.objects.select_related('paciente', 'tratamiento')

    # Por defecto: Mes actual (para coincidir con el Dashboard)
    inicio = hoy.replace(day=1)
    fin = hoy
    if fecha_inicio_str and fecha_fin_str:
        try:
            inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Aplicar filtros siempre (ya sea por defecto o por selección del usuario)
    pagos = pagos.filter(fecha__date__range=(inicio, fin))
    citas = citas.filter(fecha__range=(inicio, fin))

    if metodo_pago:
        pagos = pagos.filter(metodo=metodo_pago)

    if search_query:
        pagos = pagos.filter(Q(paciente__nombre__icontains=search_query) | Q(notas__icontains=search_query))
        citas = citas.filter(paciente__nombre__icontains=search_query)

    # 2. MÃ‰TRICAS PRINCIPALES (KPIs)
    ingresos_totales = pagos.aggregate(total=Sum('monto'))['total'] or 0
    total_facturado = citas.aggregate(total=Sum('tratamiento__precio_venta'))['total'] or 0
    deuda_total = total_facturado - ingresos_totales

    # --- DESGLOSE REVENUE SHARE (DOCTORES) ---
    pagos_con_doctor = Pago.objects.select_related('cita', 'cita__doctor', 'cita__tratamiento').filter(
        fecha__date__range=[inicio, fin]
    ).exclude(cita__doctor__isnull=True)
    
    ingresos_alquiler_espacio = 0
    pagos_a_doctores = 0
    
    for pago in pagos_con_doctor:
        if pago.cita and pago.cita.tratamiento:
            porcentaje_clinica = pago.cita.tratamiento.comision_clinica_porcentaje
        else:
            porcentaje_clinica = 30 # Porcentaje por defecto si no hay tratamiento
        parte_clinica = (pago.monto * porcentaje_clinica) / 100
        ingresos_alquiler_espacio += parte_clinica
        pagos_a_doctores += (pago.monto - parte_clinica)

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

    # 3. DATOS PARA GRÁFICOS (Sincronizados con el filtro)
    # Columna A: Flujo en el periodo seleccionado
    flujo_periodo = Pago.objects.filter(fecha__date__range=(inicio, fin)).extra(
        select={'day': "date(fecha)"}
    ).values('day').annotate(total=Sum('monto')).order_by('day')
    
    labels_flujo = [item['day'].strftime('%d %b') if isinstance(item['day'], date) else item['day'] for item in flujo_periodo]
    data_flujo = [float(item['total']) for item in flujo_periodo]

    # Columna B: Ingresos por Tratamiento en el periodo seleccionado (incluyendo abonos)
    ingresos_por_tratamiento = Pago.objects.filter(
        fecha__date__range=(inicio, fin)
    ).values(
        'cita__tratamiento__nombre'
    ).annotate(total=Sum('monto')).order_by('-total')[:5]
    
    labels_tratamientos = [item['cita__tratamiento__nombre'] or "Abonos/Otros" for item in ingresos_por_tratamiento]
    data_tratamientos = [float(item['total']) for item in ingresos_por_tratamiento]

    # 4. TABLA DE MOVIMIENTOS PRO (Aging & Status)
    movimientos = []
    # AÃ±adimos pagos realizados
    for p in pagos.order_by('-fecha')[:50]:
        movimientos.append({
            'id': p.id,
            'tipo': 'INGRESO',
            'fecha': p.fecha,
            'paciente': p.paciente,
            'concepto': p.notas or (p.cita.tratamiento.nombre if p.cita else "Pago General"),
            'monto': p.monto,
            'metodo': p.get_metodo_display(),
            'estado': 'COMPLETO',
            'es_mora': False
        })
    
    # Añadimos citas pendientes de pago (Aging > 15 días)
    limite_mora = hoy - timezone.timedelta(days=15)
    citas_pendientes = citas.filter(estado='COMPLETADA', fecha__lte=limite_mora).annotate(
        pagado=Coalesce(Sum('pagos_detalle__monto'), 0, output_field=DecimalField())
    ).filter(pagado__lt=F('tratamiento__precio_venta'))

    for c in citas_pendientes:
        movimientos.append({
            'tipo': 'DEUDA',
            'fecha': timezone.make_aware(datetime.combine(c.fecha, time.min)) if timezone.is_naive(datetime.combine(c.fecha, time.min)) else datetime.combine(c.fecha, time.min),
            'paciente': c.paciente,
            'concepto': f"Pendiente: {c.tratamiento.nombre}",
            'monto': c.tratamiento.precio_venta - c.pagado,
            'metodo': 'N/A',
            'estado': 'PENDIENTE',
            'es_mora': True
        })

    # Ordenar por fecha descendente
    movimientos.sort(key=lambda x: x['fecha'], reverse=True)

    # Ingresos Históricos (All time)
    ingresos_historicos = Pago.objects.aggregate(total=Sum('monto'))['total'] or 0

    import json
    context = {
        'ingresos_totales': ingresos_totales,
        'ingresos_historicos': ingresos_historicos,
        'ingresos_alquiler_espacio': ingresos_alquiler_espacio,
        'pagos_a_doctores': pagos_a_doctores,
        'total_facturado': total_facturado,
        'deuda_total': deuda_total,
        'tendencia_ingresos': round(tendencia_ingresos, 1),
        'gastos_fijos': gastos_fijos,
        'falta_equilibrio': falta_punto_equilibrio,
        'progreso_equilibrio': round(progreso_equilibrio, 1),
        'labels_flujo_json': json.dumps(labels_flujo),
        'data_flujo_json': json.dumps(data_flujo),
        'labels_tratamientos_json': json.dumps(labels_tratamientos),
        'data_tratamientos_json': json.dumps(data_tratamientos),
        'movimientos': movimientos,
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
        'search_query': search_query,
    }
    return render(request, 'gestion/finanzas.html', context)


@login_required
@transaction.atomic
def registrar_pago(request, pk):
    """Registra un pago/abono con cálculo de vuelto atómico"""
    paciente = get_object_or_404(Paciente, pk=pk)
    
    if request.method == 'POST':
        print(f"DEBUG: All POST keys: {list(request.POST.keys())}")
        monto = request.POST.get('monto')
        monto_recibido = request.POST.get('monto_recibido', 0)
        metodo = request.POST.get('metodo', 'EFECTIVO')
        notas = request.POST.get('notas', '')

        def clean_decimal(value):
            if not value: return Decimal('0.00')
            # Quitar símbolos de moneda, espacios y convertir comas en puntos
            v = str(value).replace('$', '').replace(' ', '').replace(',', '.').strip()
            try:
                return Decimal(v)
            except:
                return Decimal('0.00')

        monto = clean_decimal(monto)
        monto_recibido = clean_decimal(monto_recibido)
        cita_id = request.POST.get('cita_id')
        cita = None
        if cita_id:
            cita = get_object_or_404(Cita, id=cita_id)

        if monto <= 0:
            return JsonResponse({'status': 'error', 'error': 'El monto debe ser mayor a 0.'}, status=400)

        pago = Pago.objects.create(
            paciente=paciente,
            cita=cita,
            monto=monto,
            monto_recibido=monto_recibido,
            metodo=metodo,
            notas=notas or (f"Abono para {cita.tratamiento.nombre}" if cita else f"Abono registrado - {metodo}")
        )
        
        log_audit(request, "REGISTRAR_PAGO", f"Pago de {monto} para {paciente.nombre}" + (f" (Cita: {cita.tratamiento.nombre})" if cita else " (Abono General)"))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'cambio': float(pago.cambio),
                'pago_id': pago.id
            })
            
        messages.success(request, f"Pago de ${monto} registrado exitosamente.")
        return redirect('detalle_paciente', pk=pk)

    return redirect('detalle_paciente', pk=pk)


# ==========================================
# 7. INTEGRACIÓN GOOGLE CALENDAR (OAuth2)
# ==========================================

from google_auth_oauthlib.flow import Flow
from django.conf import settings

@login_required
@grupo_requerido('Doctor')
def google_calendar_init(request):
    """Inicia el flujo de autenticaciÃ³n con Google"""
    if settings.DEBUG:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

    # Google exige que la URI sea EXACTA a la registrada. Forzamos localhost global.
    host_full = request.get_host()
    if 'localhost' in host_full or '127.0.0.1' in host_full:
        base_url = "http://localhost:8000"
    else:
        base_url = f"https://{settings.TENANT_USERS_DOMAIN}"
    
    global_callback = f"{base_url}/google/callback/"

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [global_callback],
            }
        },
        scopes=['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly', 'openid', 'email', 'profile']
    )
    flow.redirect_uri = global_callback
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=f"{secrets.token_urlsafe(16)}_tenant_{request.tenant.schema_name}"
    )
    
    request.session['google_auth_state'] = state
    return redirect(authorization_url)


@login_required
@grupo_requerido('Doctor')
def google_calendar_callback(request):
    """Callback de Google para guardar las credenciales"""
    if settings.DEBUG:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
    state = request.session.get('google_auth_state')
    
    dynamic_redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    if not settings.DEBUG and 'http://' in dynamic_redirect_uri:
        dynamic_redirect_uri = dynamic_redirect_uri.replace('http://', 'https://')

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [dynamic_redirect_uri],
            }
        },
        scopes=['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly'],
        state=state
    )
    flow.redirect_uri = dynamic_redirect_uri
    
    flow.code_verifier = request.session.get('google_auth_code_verifier')
    
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
    from django.contrib.auth.models import User, Group
    request.tenant.refresh_from_db() # Forzar actualización de datos desde el esquema público
    config, created = ConfiguracionClinica.objects.get_or_create(id=1)
    google_config = GoogleCalendarConfig.objects.filter(id=1).first()

    if request.method == 'POST':
        # 1. Manejo de auto-renovación
        auto_renov = request.POST.get('auto_renovacion') == 'on'
        tenant = request.tenant
        tenant.auto_renovacion = auto_renov
        tenant.save()

        # Manejo de Crear Recepcionista
        if 'crear_recepcionista' in request.POST:
            username = request.POST.get('r_username')
            first_name = request.POST.get('r_first_name')
            last_name = request.POST.get('r_last_name')
            password = request.POST.get('r_password')
            
            clinica = request.tenant
            max_recepcionistas = 1 if clinica.plan == 'basico' else 3
            current_count = User.objects.filter(groups__name='Recepcionista').distinct().count()
            
            if not username or not password:
                messages.error(request, 'Usuario y contraseña son requeridos.')
            elif current_count >= max_recepcionistas:
                messages.error(request, f'El plan actual ({clinica.plan.capitalize()}) permite un máximo de {max_recepcionistas} recepcionista(s).')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya está en uso.')
            else:
                user = User.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    password=password
                )
                group, _ = Group.objects.get_or_create(name='Recepcionista')
                user.groups.add(group)
                messages.success(request, f'Recepcionista {username} creada con éxito.')
                log_audit(request, "CREAR_RECEPCIONISTA", f"Recepcionista {username} creada por doctor")
            return redirect('/configuracion/#tab-recepcionistas')

        # Manejo de Eliminar Recepcionista
        if 'eliminar_recepcionista' in request.POST:
            r_id = request.POST.get('r_id')
            try:
                user_to_delete = User.objects.get(id=r_id)
                if not user_to_delete.is_superuser:
                    user_to_delete.delete()
                    messages.success(request, 'Recepcionista eliminada con éxito.')
                    log_audit(request, "ELIMINAR_RECEPCIONISTA", f"Recepcionista {user_to_delete.username} eliminada por doctor")
                else:
                    messages.error(request, 'No puedes eliminar a un usuario administrador.')
            except User.DoesNotExist:
                messages.error(request, 'No se encontró la recepcionista.')
            return redirect('/configuracion/#tab-recepcionistas')

        # 2. Manejo de Cambio de Contraseña
        if 'cambiar_password' in request.POST:
            old_pass = request.POST.get('current_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')

            if not request.user.check_password(old_pass):
                messages.error(request, 'La contraseña actual es incorrecta.')
            elif new_pass != confirm_pass:
                messages.error(request, 'Las nuevas contraseñas no coinciden.')
            elif len(new_pass) < 6:
                messages.error(request, 'La nueva contraseña debe tener al menos 6 caracteres.')
            else:
                request.user.set_password(new_pass)
                request.user.save()
                update_session_auth_hash(request, request.user) # No cerrar sesión
                log_audit(request, "CAMBIO_PASSWORD", "Usuario actualizó su contraseña")
                messages.success(request, '¡Contraseña actualizada con éxito!')
            return redirect('/configuracion/#tab-security')

        # 3. Manejo de Formulario General
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
            log_audit(request, "UPDATE_CONFIG", "Actualización de parámetros generales")
            messages.success(request, '¡Configuración actualizada con éxito!')
            return redirect('panel_configuracion')
    else:
        form = ConfiguracionClinicaForm(instance=config)

    context = {
        'form': form,
        'config': config,
        'google_config': google_config,
        'suscripciones': request.tenant.suscripciones.all().order_by('-fecha_inicio'),
        'dias': ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo'],
        'audit_logs': LogActividad.objects.all()[:50], # Últimos 50 logs
        'recepcionistas': User.objects.filter(groups__name='Recepcionista').distinct(),
        'max_recepcionistas': 1 if request.tenant.plan == 'basico' else 3
    }
    return render(request, 'gestion/configuraciones.html', context)


@login_required
@grupo_requerido('Doctor')
def gestion_doctores(request):
    """CRUD de Staff con límites por plan"""
    clinica = request.tenant
    max_drs = 3 if clinica.plan == 'basico' else 5
    doctores = DoctorColaborador.objects.all()
    count = doctores.count()

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        
        # Eliminar
        if doctor_id and 'eliminar' in request.POST:
            doctor = get_object_or_404(DoctorColaborador, pk=doctor_id)
            nombre = doctor.nombre
            doctor.delete()
            messages.success(request, f"{nombre} eliminado correctamente.")
            return redirect('gestion_doctores')

        # Editar
        if doctor_id:
            doctor = get_object_or_404(DoctorColaborador, pk=doctor_id)
            doctor.nombre = request.POST.get('nombre')
            doctor.especialidad = request.POST.get('especialidad')
            doctor.telefono = request.POST.get('telefono')
            doctor.email = request.POST.get('email')
            doctor.color_agenda = request.POST.get('color_agenda', '#3b82f6')
            doctor.save()
            messages.success(request, f"{doctor.nombre} actualizado correctamente.")
            return redirect('gestion_doctores')

        # Crear
        if count >= max_drs:
            messages.error(request, f"Límite de staff alcanzado. Tu plan {clinica.plan.upper()} solo permite {max_drs} doctores.")
            return redirect('gestion_doctores')
        
        nombre = request.POST.get('nombre')
        especialidad = request.POST.get('especialidad')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')
        color = request.POST.get('color_agenda', '#3b82f6')
        
        DoctorColaborador.objects.create(
            nombre=nombre,
            especialidad=especialidad,
            telefono=telefono,
            email=email,
            color_agenda=color
        )
        messages.success(request, f"{nombre} registrado exitosamente.")
        return redirect('gestion_doctores')

    return render(request, 'gestion/staff.html', {
        'doctores': doctores,
        'max_drs': max_drs,
        'count': count,
        'porcentaje_uso': (count / max_drs) * 100
    })


def enviar_recordatorio_whatsapp(paciente, cita):
    """Motor de recordatorios por WhatsApp"""
    config = ConfiguracionClinica.objects.first()
    if not config or not config.whatsapp_recordatorios_activos:
        return False
    if not paciente.telefono:
        return False
    # Simulación de envío
    print(f"WS-PUSH: {paciente.telefono} -> Cita {cita.fecha}")
    return True


@login_required
@grupo_requerido('Doctor')
def descargar_respaldo(request):
    """Permite descargar el archivo db.sqlite3 actual"""
    import os
    from django.http import FileResponse, Http404
    from django.conf import settings

    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    
    if os.path.exists(db_path):
        response = FileResponse(open(db_path, 'rb'), content_type='application/x-sqlite3')
        response['Content-Disposition'] = f'attachment; filename="respaldo_densaas_{timezone.now().strftime("%Y%m%d")}.sqlite3"'
        log_audit(request, "BACKUP_DOWNLOAD", "Usuario descargó respaldo de base de datos")
        return response
    else:
        raise Http404("Base de datos no encontrada")

