from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Clinica, Dominio

@admin.register(Clinica)
class ClinicaAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('nombre_clinica', 'schema_name', 'creado_en', 'plan')
    search_fields = ('nombre_clinica', 'schema_name')

@admin.register(Dominio)
class DominioAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    search_fields = ('domain',)
