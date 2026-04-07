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
    path('tratamientos/', views.lista_tratamientos, name='lista_tratamientos'),
    path('tratamientos/nuevo/', views.gestionar_tratamiento, name='nuevo_tratamiento'),
    path('tratamientos/<int:pk>/editar/', views.gestionar_tratamiento, name='editar_tratamiento'),
    path('pacientes/<int:pk>/pagos/nuevo/', views.registrar_pago, name='registrar_pago'),
    path('pacientes/<int:pk>/archivos/subir/', views.subir_archivo, name='subir_archivo'),
    path('calendario/', views.calendario, name='calendario'),
    path('api/citas/', views.citas_json, name='citas_json'),
    path('pacientes/<int:pk>/receta/nueva/', views.nueva_receta, name='nueva_receta'),
    path('recetas/<int:pk>/imprimir/', views.imprimir_receta, name='imprimir_receta'),
    path('pacientes/exportar/excel/', views.exportar_pacientes_excel, name='exportar_excel'),
    path('pacientes/<int:pk>/estado-cuenta/', views.estado_cuenta_pdf, name='estado_cuenta'),
    path('inventario/', views.lista_inventario, name='inventario'),
]