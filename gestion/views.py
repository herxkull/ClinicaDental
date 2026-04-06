from django.shortcuts import render, get_object_or_404
from .models import Paciente, Cita
from datetime import date
from django.shortcuts import redirect
from .forms import PacienteForm, CitaForm, DienteEstadoForm, DienteEstado, TratamientoForm, PagoForm, ArchivoPacienteForm
from django.db.models import Sum, Q
from .models import Tratamiento, Pago, ArchivoPaciente
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    hoy = date.today()

    # 1. Contadores básicos
    total_pacientes = Paciente.objects.count()

    # 2. Citas de hoy y proyección financiera
    citas_hoy_lista = Cita.objects.filter(fecha=hoy).order_by('hora')
    citas_hoy_count = citas_hoy_lista.count()

    # Sumamos el 'costo_base' de los tratamientos de las citas de hoy
    ingresos_esperados = citas_hoy_lista.aggregate(total=Sum('tratamiento__costo_base'))['total']
    if ingresos_esperados is None:
        ingresos_esperados = 0  # Si no hay citas, los ingresos son 0

    ultimos_pacientes = Paciente.objects.all().order_by('-id')[:5]

    context = {
        'total_pacientes': total_pacientes,
        'citas_hoy': citas_hoy_count,
        'citas_hoy_lista': citas_hoy_lista,
        'ingresos_esperados': ingresos_esperados,
        'ultimos_pacientes': ultimos_pacientes,
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
    # Capturamos lo que el usuario escriba en la barra de búsqueda
    query = request.GET.get('q')

    if query:
        # Buscamos si el texto coincide con el nombre O con la cédula
        pacientes = Paciente.objects.filter(
            Q(nombre__icontains=query) | Q(cedula__icontains=query)
        ).order_by('nombre')
    else:
        # Si no hay búsqueda, mostramos todos
        pacientes = Paciente.objects.all().order_by('nombre')

    return render(request, 'gestion/lista_pacientes.html', {
        'pacientes': pacientes,
        'query': query  # Mandamos el texto de vuelta para que no se borre de la barra
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

    # --- LÓGICA DEL ODONTOGRAMA (Mantén tu código anterior del request.POST aquí) ---
    if request.method == 'POST':
        form_diente = DienteEstadoForm(request.POST)
        if form_diente.is_valid():
            num_diente = form_diente.cleaned_data['diente']
            DienteEstado.objects.update_or_create(
                paciente=paciente, diente=num_diente,
                defaults={'estado': form_diente.cleaned_data['estado'], 'notas': form_diente.cleaned_data['notas']}
            )
            return redirect('detalle_paciente', pk=paciente.pk)
    else:
        form_diente = DienteEstadoForm()

    dientes_registrados = paciente.odontograma.all()
    diccionario_dientes = {d.diente: d.estado for d in dientes_registrados}
    # ----------------------------------------------------------------------------------

    # --- NUEVA LÓGICA FINANCIERA ---
    # Sumamos el costo de todos los tratamientos de sus citas
    total_tratamientos = citas.aggregate(total=Sum('tratamiento__costo_base'))['total'] or 0
    # Traemos todos sus pagos y los sumamos
    pagos = Pago.objects.filter(paciente=paciente).order_by('-fecha')
    total_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0
    # Calculamos cuánto debe
    saldo_pendiente = total_tratamientos - total_pagos

    return render(request, 'gestion/detalle_paciente.html', {
        'paciente': paciente,
        'citas': citas,
        'form_diente': form_diente,
        'estados_dientes': diccionario_dientes,
        'dientes_detalle': dientes_registrados,
        # Pasamos las nuevas variables al HTML
        'total_tratamientos': total_tratamientos,
        'total_pagos': total_pagos,
        'saldo_pendiente': saldo_pendiente,
        'pagos': pagos
    })

def lista_tratamientos(request):
    tratamientos = Tratamiento.objects.all().order_by('nombre')
    return render(request, 'gestion/lista_tratamientos.html', {'tratamientos': tratamientos})

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
# Create your views here.
