from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('pacientes/', views.lista_pacientes, name='lista_pacientes'),
    path('pacientes/nuevo/', views.nuevo_paciente, name='nuevo_paciente'),
    path('citas/', views.lista_citas, name='lista_citas'),
    path('citas/nueva/', views.nueva_cita, name='nueva_cita'),
    path('pacientes/<int:pk>/', views.detalle_paciente, name='detalle_paciente'),
    path('pacientes/<int:pk>/editar/', views.editar_paciente, name='editar_paciente'),
path('citas/<int:pk>/toggle-completada/', views.completar_cita, name='completar_cita'),
]