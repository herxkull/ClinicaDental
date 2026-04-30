from django.db import models
from django.conf import settings
import uuid

class DoctorColaborador(models.Model):
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    color_agenda = models.CharField(max_length=7, default="#3b82f6", help_text="Color para identificar sus citas")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.nombre} ({self.especialidad})"


class Paciente(models.Model):
    # Datos Personales
    nombre = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)

    # Antecedentes Médicos
    alergias = models.TextField(help_text="Ej: Penicilina, Anestesia", blank=True)
    diabetes = models.BooleanField(default=False)
    hipertension = models.BooleanField(default=False)
    notas_medicas = models.TextField(verbose_name="Antecedentes generales", blank=True)

    # Odontograma Moderno (Guarda todo el estado visual de los dientes en formato JSON)
    odontograma_data = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.cedula}"


class Tratamiento(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio cobrado al paciente")
    color = models.CharField(max_length=7, default="#3b82f6", help_text="Color en formato HEX")
    comision_clinica_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=30.00, help_text="Porcentaje que se queda la clínica (ej: 30.00)")
    doctor_referencia = models.ForeignKey('DoctorColaborador', on_delete=models.SET_NULL, null=True, blank=True, help_text="Doctor que suele realizar este tratamiento")

    def __str__(self):
        return self.nombre

    @property
    def costo_materiales(self):
        total = sum(item.producto.costo_unitario * item.cantidad_usada for item in self.materiales.all())
        return total

    @property
    def margen_ganancia(self):
        return self.precio_venta - self.costo_materiales

    @property
    def margen_porcentaje(self):
        if self.precio_venta > 0:
            return (self.margen_ganancia / self.precio_venta) * 100
        return 0


class Cita(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    # Agregamos related_name='citas' para búsquedas más rápidas
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    doctor = models.ForeignKey(DoctorColaborador, on_delete=models.SET_NULL, null=True, blank=True, related_name='citas')
    tratamiento = models.ForeignKey(Tratamiento, on_delete=models.SET_NULL, null=True)
    fecha = models.DateField(db_index=True)
    hora = models.TimeField()
    motivo = models.TextField()
    observaciones_doctor = models.TextField(blank=True)
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='PENDIENTE', 
        db_index=True
    )
    
    # Campo para sincronización con Google Calendar
    google_event_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.paciente.nombre} - {self.fecha.strftime('%d/%m/%Y')}"

    @property
    def badge_class(self):
        classes = {
            'PENDIENTE': 'bg-gray-500',
            'CONFIRMADA': 'bg-blue-500',
            'COMPLETADA': 'bg-green-500',
            'CANCELADA': 'bg-red-500',
        }
        return classes.get(self.estado, 'bg-gray-500')


class Pago(models.Model):
    METODOS_PAGO = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Para calcular el cambio")
    metodo = models.CharField(max_length=20, choices=METODOS_PAGO, default='EFECTIVO')
    cita = models.ForeignKey('Cita', on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_detalle')
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    notas = models.CharField(max_length=200, blank=True, null=True, help_text="Referencia o detalle extra")

    @property
    def cambio(self):
        if self.monto_recibido > 0:
            return self.monto_recibido - self.monto
        return 0

    def __str__(self):
        return f"{self.paciente.nombre} - ${self.monto} ({self.get_metodo_display()})"


class ArchivoPaciente(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='archivos')
    titulo = models.CharField(max_length=100, help_text="Ej. Radiografía Panorámica, Examen de Sangre...")
    archivo = models.FileField(upload_to='pacientes_archivos/')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.paciente.nombre}"


class Receta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='recetas')
    fecha = models.DateTimeField(auto_now_add=True)
    prescripcion = models.TextField(help_text="Ej: Ibuprofeno 400mg - 1 pastilla cada 8 horas por 3 días")
    notas_adicionales = models.TextField(blank=True, null=True, help_text="Recomendaciones (reposo, dieta, etc.)")

    def __str__(self):
        return f"Receta de {self.paciente.nombre} - {self.fecha.strftime('%d/%m/%Y')}"


class Producto(models.Model):
    CATEGORIAS = [
        ('DESECHABLES', 'Desechables'),
        ('INSTRUMENTAL', 'Instrumental'),
        ('ANESTESIA', 'Anestesia'),
        ('MATERIAL_RELLENO', 'Material de Relleno'),
        ('LIMPIEZA', 'Limpieza/Desinfección'),
        ('OTROS', 'Otros'),
    ]
    nombre = models.CharField(max_length=100, db_index=True)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='OTROS')
    descripcion = models.TextField(blank=True, null=True)
    cantidad_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    precio_venta_sugerido = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.categoria}] {self.nombre} (Stock: {self.cantidad_actual})"

class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('ENTRADA', 'Entrada por Compra'),
        ('SALIDA', 'Salida por Uso'),
        ('AJUSTE', 'Ajuste (Pérdida/Daño)'),
    ]
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    notas = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    @property
    def total_valor_stock(self):
        return self.cantidad_actual * self.costo_unitario

    @property
    def necesita_reabastecimiento(self):
        return self.cantidad_actual <= self.stock_minimo


class MaterialTratamiento(models.Model):
    tratamiento = models.ForeignKey(Tratamiento, on_delete=models.CASCADE, related_name='materiales')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_usada = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad_usada}x {self.producto.nombre} para {self.tratamiento.nombre}"


class GoogleCalendarConfig(models.Model):
    calendar_id = models.CharField(max_length=255, default='primary')
    credentials_json = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    last_sync = models.DateTimeField(null=True, blank=True)


class ConfiguracionClinica(models.Model):
    # General
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    nombre_comercial = models.CharField(max_length=100, blank=True)
    direccion = models.TextField(blank=True)
    telefono_contacto = models.CharField(max_length=20, blank=True)
    email_contacto = models.EmailField(blank=True)

    # Clínica
    duracion_cita_estandar = models.IntegerField(default=60)
    horarios_atencion = models.JSONField(default=dict, blank=True)
    
    # Finanzas
    moneda_simbolo = models.CharField(max_length=5, default='$')
    impuesto_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    pie_pagina_recibo = models.TextField(blank=True)

    # WhatsApp
    whatsapp_numero = models.CharField(max_length=20, blank=True)
    whatsapp_recordatorios_activos = models.BooleanField(default=False)

    def __str__(self):
        return f"Configuración de {self.nombre_comercial or 'la Clínica'}"


class LogActividad(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=100)
    detalles = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Log de Actividad"
        verbose_name_plural = "Logs de Actividad"

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y %H:%M')} - {self.usuario} - {self.accion}"
