from django.db import models

# Create your models here.
# clientes/models.py
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Clinica(TenantMixin):
    # TenantMixin ya incluye un campo 'schema_name' por defecto
    nombre_clinica = models.CharField(max_length=100)
    creado_en = models.DateField(auto_now_add=True)

    # El plan que pagan (opcional para el futuro)
    plan = models.CharField(max_length=50, default='basico')

    # Esto le dice a Django que cree las tablas automáticamente al registrar la clínica
    auto_create_schema = True

    def __str__(self):
        return self.nombre_clinica

class Dominio(DomainMixin):
    # DomainMixin ya trae 'domain' y 'is_primary'
    pass