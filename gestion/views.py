from django.shortcuts import render, get_object_or_404
from .models import Paciente, Cita
from datetime import date
from django.shortcuts import redirect
from .forms import PacienteForm
from .forms import CitaForm
from .forms import DienteEstadoForm
from .models import DienteEstado
from django.db.models import Sum
from django.db.models import Q

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

    # Procesar el formulario de actualización de dientes
    if request.method == 'POST':
        form_diente = DienteEstadoForm(request.POST)
        if form_diente.is_valid():
            num_diente = form_diente.cleaned_data['diente']
            # update_or_create busca si el diente ya tiene registro, si lo tiene lo actualiza, si no, lo crea.
            DienteEstado.objects.update_or_create(
                paciente=paciente,
                diente=num_diente,
                defaults={
                    'estado': form_diente.cleaned_data['estado'],
                    'notas': form_diente.cleaned_data['notas']
                }
            )
            return redirect('detalle_paciente', pk=paciente.pk)
    else:
        form_diente = DienteEstadoForm()

    # Traer todos los dientes registrados para colorear el odontograma
    dientes_registrados = paciente.odontograma.all()
    # Convertimos los datos en un diccionario {11: 'Caries', 12: 'Sano'} para usarlo fácil en el HTML
    diccionario_dientes = {d.diente: d.estado for d in dientes_registrados}

    return render(request, 'gestion/detalle_paciente.html', {
        'paciente': paciente,
        'citas': citas,
        'form_diente': form_diente,
        'estados_dientes': diccionario_dientes,
        'dientes_detalle': dientes_registrados
    })
# Create your views here.
