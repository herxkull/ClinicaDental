from django.db import models


# Create your models here.
class Paciente(models.Model):
    # Datos Personales
    nombre = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)

    # Antecedentes Médicos (Lo que el dentista DEBE saber)
    alergias = models.TextField(help_text="Ej: Penicilina, Anestesia", blank=True)
    diabetes = models.BooleanField(default=False)
    hipertension = models.BooleanField(default=False)
    notas_medicas = models.TextField(verbose_name="Antecedentes generales", blank=True)

    def __str__(self):
        return f"{self.nombre} - {self.cedula}"

class DienteEstado(models.Model):
    # Opciones de estado (puedes añadir más luego)
    ESTADOS_CHOICES = [
        ('SANO', 'Sano'),
        ('CARIES', 'Caries'),
        ('CORONA', 'Corona'),
        ('AUSENTE', 'Ausente'),
        ('TRATADO', 'Tratado Endodoncia'),
        ('IMPLANTE', 'Implante'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='odontograma')
    numero_diente = models.IntegerField(help_text="Número internacional del diente (11-48)")
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='SANO')
    notas = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('paciente', 'numero_diente') # Un paciente solo puede tener un registro por diente
        ordering = ['numero_diente']

    def __str__(self):
        return f"Diente {self.numero_diente} - {self.get_estado_display()} ({self.paciente.nombre})"

class Tratamiento(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    costo_base = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre


class Cita(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    tratamiento = models.ForeignKey(Tratamiento, on_delete=models.SET_NULL, null=True)
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.TextField()
    observaciones_doctor = models.TextField(blank=True)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.paciente.nombre} - {self.fecha}"




class Pago(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True) # Guarda la fecha y hora automáticamente
    notas = models.CharField(max_length=200, blank=True, null=True, help_text="Ej. Efectivo, Transferencia, Tarjeta...")

    def __str__(self):
        return f"{self.paciente.nombre} - ${self.monto} ({self.fecha.strftime('%d/%m/%Y')})"


class ArchivoPaciente(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='archivos')
    titulo = models.CharField(max_length=100, help_text="Ej. Radiografía Panorámica, Examen de Sangre...")
    archivo = models.FileField(upload_to='pacientes_archivos/')
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
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    cantidad_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)  # Para alertas
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.cantidad_actual})"

    @property
    def necesita_reabastecimiento(self):
        return self.cantidad_actual <= self.stock_minimo

class MaterialTratamiento(models.Model):
    tratamiento = models.ForeignKey('Tratamiento', on_delete=models.CASCADE, related_name='materiales')
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad_usada = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad_usada} de {self.producto.nombre} para {self.tratamiento.nombre}"

class ArchivoPaciente(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='archivos')
    titulo = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='pacientes/evidencia/', null=True, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.paciente.nombre}"

