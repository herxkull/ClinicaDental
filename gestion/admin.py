from django.contrib import admin
from .models import Paciente, Cita, Tratamiento, Producto, MaterialTratamiento, ArchivoPaciente

# --- Configuración del panel de Pacientes ---
@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula', 'telefono', 'diabetes', 'hipertension')
    search_fields = ('nombre', 'cedula')
    list_filter = ('diabetes', 'hipertension')
    fieldsets = (
        ('Datos Personales', {
            'fields': ('nombre', 'cedula', 'fecha_nacimiento', 'telefono', 'email')
        }),
        ('Información Médica', {
            'fields': ('alergias', 'diabetes', 'hipertension', 'notas_medicas')
        }),
    )

# --- Configuración del panel de PRODUCTOS (Inventario) ---
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad_actual', 'stock_minimo', 'precio_compra')
    list_filter = ('nombre',)
    search_fields = ('nombre',)

# --- Configuración para conectar Materiales con Tratamientos ---
class MaterialInline(admin.TabularInline):
    model = MaterialTratamiento
    extra = 1

# --- Configuración del panel de Tratamientos (CON INLINES) ---
@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    inlines = [MaterialInline] # Esto permite agregar materiales dentro del tratamiento
    list_display = ('nombre', 'costo_base')
    search_fields = ('nombre',)

# --- Configuración del panel de Citas ---
@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'tratamiento', 'fecha', 'hora', 'completada')
    list_filter = ('fecha', 'completada', 'tratamiento')
    date_hierarchy = 'fecha'

@admin.register(ArchivoPaciente)
class ArchivoPacienteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'paciente', 'fecha_subida')
    list_filter = ('paciente',)