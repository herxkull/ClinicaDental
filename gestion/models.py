from django.db import models


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
    costo_base = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre


class Cita(models.Model):
    # Agregamos related_name='citas' para búsquedas más rápidas
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    tratamiento = models.ForeignKey(Tratamiento, on_delete=models.SET_NULL, null=True)
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.TextField()
    observaciones_doctor = models.TextField(blank=True)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.paciente.nombre} - {self.fecha.strftime('%d/%m/%Y')}"


class Pago(models.Model):
    METODOS_PAGO = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    # ¡AQUÍ ESTÁ LA MAGIA! Agregamos el método de pago correctamente
    metodo = models.CharField(max_length=20, choices=METODOS_PAGO, default='EFECTIVO')
    fecha = models.DateTimeField(auto_now_add=True)
    notas = models.CharField(max_length=200, blank=True, null=True, help_text="Referencia o detalle extra")

    def __str__(self):
        return f"{self.paciente.nombre} - ${self.monto} ({self.get_metodo_display()})"


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
    stock_minimo = models.IntegerField(default=5)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} (Stock: {self.cantidad_actual})"

    @property
    def necesita_reabastecimiento(self):
        return self.cantidad_actual <= self.stock_minimo


class MaterialTratamiento(models.Model):
    tratamiento = models.ForeignKey(Tratamiento, on_delete=models.CASCADE, related_name='materiales')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_usada = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad_usada}x {self.producto.nombre} para {self.tratamiento.nombre}"