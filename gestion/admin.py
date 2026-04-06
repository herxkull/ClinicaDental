from django.contrib import admin
from .models import Paciente, Cita, Tratamiento

# Configuración del panel de Pacientes
@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    # Columnas que se ven en la lista principal
    list_display = ('nombre', 'cedula', 'telefono', 'diabetes', 'hipertension')
    # Buscador por nombre y cédula
    search_fields = ('nombre', 'cedula')
    # Filtros laterales para encontrar rápido a pacientes con condiciones médicas
    list_filter = ('diabetes', 'hipertension')
    # Organización de los campos al editar un paciente
    fieldsets = (
        ('Datos Personales', {
            'fields': ('nombre', 'cedula', 'fecha_nacimiento', 'telefono', 'email')
        }),
        ('Información Médica', {
            'fields': ('alergias', 'diabetes', 'hipertension', 'notas_medicas')
        }),
    )

# Configuración del panel de Tratamientos
@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'costo_base')
    search_fields = ('nombre',)

# Configuración del panel de Citas
@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'tratamiento', 'fecha', 'hora', 'completada')
    list_filter = ('fecha', 'completada', 'tratamiento')
    date_hierarchy = 'fecha' # Agrega una barra de navegación por fechas arriba