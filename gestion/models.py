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