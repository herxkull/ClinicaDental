from django.shortcuts import render
from .models import Paciente, Cita
from datetime import date
from django.shortcuts import redirect
from .forms import PacienteForm

def dashboard(request):
    # Contamos los datos de la base de datos
    total_pacientes = Paciente.objects.count()
    citas_hoy = Cita.objects.filter(fecha=date.today()).count()
    ultimos_pacientes = Paciente.objects.all().order_by('-id')[:5]  # Los últimos 5 registrados

    context = {
        'total_pacientes': total_pacientes,
        'citas_hoy': citas_hoy,
        'ultimos_pacientes': ultimos_pacientes,
    }

    return render(request, 'gestion/dashboard.html', context)


# Vista para listar pacientes
def lista_pacientes(request):
    pacientes = Paciente.objects.all()
    return render(request, 'gestion/lista_pacientes.html', {'pacientes': pacientes})

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

# Create your views here.
