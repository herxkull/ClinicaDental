from django.contrib import admin
from .models import Paciente, Cita, Tratamiento, Producto, MaterialTratamiento, ArchivoPaciente, Pago, Receta, DoctorColaborador, ConfiguracionClinica, MovimientoInventario
from django.utils.html import format_html


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
            # Agregamos odontograma_data aquí para que no se pierda en el admin
            'fields': ('alergias', 'diabetes', 'hipertension', 'notas_medicas', 'odontograma_data')
        }),
    )

# --- Configuración del panel de PRODUCTOS (Inventario) ---
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad_actual', 'stock_minimo', 'costo_unitario', 'precio_venta_sugerido')
    list_filter = ('nombre',)
    search_fields = ('nombre',)

# --- Configuración para conectar Materiales con Tratamientos ---
class MaterialInline(admin.TabularInline):
    model = MaterialTratamiento
    extra = 1

# --- Configuración del panel de Tratamientos (CON INLINES) ---
@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    inlines = (MaterialInline,) # Esto permite agregar materiales dentro del tratamiento
    list_display = ('nombre', 'precio_venta')
    search_fields = ('nombre',)

# --- Configuración del panel de Citas ---
@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'tratamiento', 'fecha', 'hora', 'estado')
    list_filter = ('fecha', 'estado', 'tratamiento')
    date_hierarchy = 'fecha'

@admin.register(ArchivoPaciente)
class ArchivoPacienteAdmin(admin.ModelAdmin):
    list_display = ('preview', 'titulo', 'paciente', 'fecha_subida')
    list_filter = ('paciente',)
    readonly_fields = ('preview_large',)

    def preview(self, obj):
        if obj.archivo and obj.archivo.url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 8px; object-fit: cover;" />', obj.archivo.url)
        return "Archivo"
    preview.short_description = 'Vista Previa'

    def preview_large(self, obj):
        if obj.archivo:
            return format_html('<img src="{}" style="max-width: 500px; border-radius: 12px; shadow: 0 4px 6px rgba(0,0,0,0.1);" />', obj.archivo.url)
        return "Sin archivo"
    preview_large.short_description = 'Vista Ampliada'

@admin.register(DoctorColaborador)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especialidad', 'color_dot', 'is_active')
    
    def color_dot(self, obj):
        return format_html('<div style="width: 20px; height: 20px; border-radius: 50%; background: {};"></div>', obj.color_agenda)
    color_dot.short_description = 'Color'

@admin.register(ConfiguracionClinica)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ('id', 'logo_preview', 'whatsapp_recordatorios_activos')
    
    def logo_preview(self, obj):
        if obj.logo_clinica:
            return format_html('<img src="{}" style="height: 30px;" />', obj.logo_clinica.url)
        return "No logo"

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'stock_nuevo', 'usuario', 'fecha')
    list_filter = ('tipo', 'fecha', 'usuario')
    search_fields = ('producto__nombre', 'notas')

# --- Configuración de Pagos y Recetas ---
@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'monto', 'metodo', 'fecha')
    list_filter = ('metodo', 'fecha')
    search_fields = ('paciente__nombre',)

@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha')
    search_fields = ('paciente__nombre',)