from django.db import models

# Create your models here.
# clientes/models.py
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Clinica(TenantMixin):
    nombre_clinica = models.CharField(max_length=100)
    email_contacto = models.EmailField(max_length=100, blank=True, null=True)
    creado_en = models.DateField(auto_now_add=True)

    # Estado Maestro de la Clínica
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=True)
    trial_start_date = models.DateTimeField(auto_now_add=True)
    trial_end_date = models.DateTimeField(blank=True, null=True)

    # Datos Financieros
    plan = models.CharField(max_length=50, default='basico') # 'basico', 'pro'
    gastos_fijos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    auto_renovacion = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.trial_end_date:
            from django.utils import timezone
            self.trial_end_date = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def trial_expirado(self):
        from django.utils import timezone
        return timezone.now() > self.trial_end_date if self.trial_end_date else False

    @property
    def dias_restantes(self):
        from django.utils import timezone
        if not self.trial_end_date: return 0
        diff = self.trial_end_date - timezone.now()
        return max(0, diff.days)

    @property
    def suscripcion_activa(self):
        """Verifica si hay una suscripción aprobada o de cortesía que no ha vencido"""
        from django.utils import timezone
        return self.suscripciones.filter(
            estado_pago__in=['APROBADO', 'CORTESIA'], 
            fecha_vencimiento__gt=timezone.now()
        ).exists()

    def __str__(self):
        return self.nombre_clinica

class Suscripcion(models.Model):
    PLAN_CHOICES = [('BASICO', 'Básico'), ('PRO', 'Profesional')]
    ESTADO_CHOICES = [
        ('TRIAL', 'Periodo de Prueba'),
        ('CORTESIA', 'Cortesía (Mes de Prueba)'),
        ('PENDIENTE', 'Pendiente de Pago'),
        ('VALIDACION', 'Pendiente de Validación (Manual)'),
        ('APROBADO', 'Aprobado / Activo'),
        ('RECHAZADO', 'Rechazado / Expirado'),
    ]
    METODO_CHOICES = [
        ('2CHECKOUT', 'Tarjeta (2Checkout)'), 
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CORTESIA', 'Mes de Cortesía'),
        ('GRATIS', 'Periodo de Prueba (Trial)')
    ]

    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name='suscripciones')
    plan_tipo = models.CharField(max_length=20, choices=PLAN_CHOICES, default='PRO')
    estado_pago = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    metodo_pago = models.CharField(max_length=20, choices=METODO_CHOICES)
    
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField(blank=True, null=True)
    
    # Solo para transferencias
    comprobante_img = models.ImageField(upload_to='comprobantes/%Y/%m/', blank=True, null=True)
    notas_admin = models.TextField(blank=True, null=True)
    
    # 2Checkout Reference
    external_reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.clinica.nombre_clinica} - {self.plan_tipo} ({self.estado_pago})"

class Dominio(DomainMixin):
    pass