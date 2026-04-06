from django.shortcuts import render
from .models import Paciente, Cita
from datetime import date


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


from django.shortcuts import render

# Create your views here.
