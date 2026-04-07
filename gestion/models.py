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


class DienteEstado(models.Model):
        paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='odontograma')
        diente = models.IntegerField()  # Usaremos los números FDI (11-18, 21-28, etc.)

        ESTADOS = [
            ('Sano', 'Sano'),
            ('Caries', 'Caries (Rojo)'),
            ('Resina', 'Resina/Empaste (Azul)'),
            ('Extraccion', 'Para Extracción (Naranja)'),
            ('Ausente', 'Ausente (Negro)'),
            ('Corona', 'Corona (Amarillo)')
        ]
        estado = models.CharField(max_length=20, choices=ESTADOS, default='Sano')
        notas = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: Cara oclusal, dolor agudo...")

        class Meta:
            # Esto evita que guardemos dos veces el estado del mismo diente para el mismo paciente
            unique_together = ('paciente', 'diente')

        def __str__(self):
            return f"Diente {self.diente} - {self.estado}"

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