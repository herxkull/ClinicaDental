from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('pacientes/', views.lista_pacientes, name='lista_pacientes'),
    path('pacientes/nuevo/', views.nuevo_paciente, name='nuevo_paciente'),
]