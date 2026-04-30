# clientes/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Q
from .models import Clinica, Suscripcion, Dominio

# --- CONFIGURACIÓN GLOBAL DEL ADMIN ---
admin.site.site_header = "DenSaaS Master Console"
admin.site.site_title = "Admin Maestro"
admin.site.index_title = "Métricas de Crecimiento"

# Inyectar métricas en el index original
def custom_index(request, extra_context=None):
    if not request.user.is_superuser:
        return redirect('/logout/') # Seguridad para el esquema público
        
    mrr = Suscripcion.objects.filter(estado_pago__in=['APROBADO', 'CORTESIA']).count() * 49.99
    registros_hoy = Clinica.objects.filter(trial_start_date__gte=timezone.now() - timedelta(days=1)).count()
    
    extra_context = extra_context or {}
    extra_context['kpis'] = [
        {'label': 'MRR Estimado', 'value': f"${mrr:,.2f}", 'icon': '💰', 'color': 'text-green-600'},
        {'label': 'Nuevos (24h)', 'value': registros_hoy, 'icon': '🚀', 'color': 'text-blue-600'},
        {'label': 'Total Clínicas', 'value': Clinica.objects.count(), 'icon': '🏢', 'color': 'text-gray-800'},
    ]
    # Usamos el index original pero con nuestro contexto
    from django.contrib.admin.sites import AdminSite
    return AdminSite.index(admin.site, request, extra_context)

# Sobreescribir el index del sitio por defecto
admin.site.index = custom_index.__get__(admin.site, admin.site.__class__)

# --- INLINES ---

class DominioInline(admin.TabularInline):
    model = Dominio
    extra = 1
    fields = ('domain', 'is_primary')

class SuscripcionInline(admin.TabularInline):
    model = Suscripcion
    extra = 0
    fields = ('plan_tipo', 'estado_pago', 'metodo_pago', 'fecha_vencimiento')
    ordering = ('-fecha_inicio',)

# --- FILTROS ---

class ExpiracionFiltro(admin.SimpleListFilter):
    title = 'Próximas Expiraciones'
    parameter_name = 'expiracion'

    def lookups(self, request, model_admin):
        return (
            ('3_dias', 'Expira en 3 días'),
            ('7_dias', 'Expira en 7 días'),
        )

    def queryset(self, request, queryset):
        hoy = timezone.now()
        if self.value() == '3_dias':
            return queryset.filter(fecha_vencimiento__range=[hoy, hoy + timedelta(days=3)])
        if self.value() == '7_dias':
            return queryset.filter(fecha_vencimiento__range=[hoy, hoy + timedelta(days=7)])

# --- MODEL ADMINS ---

@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    list_display = ('nombre_clinica', 'display_subdominio', 'get_plan_badge', 'vigencia_color', 'is_active', 'view_on_site_btn')
    list_filter = ('is_active', 'is_trial', 'plan')
    search_fields = ('nombre_clinica', 'schema_name')
    inlines = [DominioInline, SuscripcionInline]
    actions = ['extender_trial_7_dias', 'suspender_clinica']

    @admin.display(description='Vigencia', ordering='trial_end_date')
    def vigencia_color(self, obj):
        dias = obj.dias_restantes
        icon = ""
        if obj.is_trial and dias <= 2:
            icon = "⚠️ "
        color = "#ef4444" if dias < 5 else "#10b981"
        return format_html('<span style="color: {}; font-weight: bold;">{}{} días</span>', color, icon, dias)

    @admin.display(description='URL')
    def view_on_site_btn(self, obj):
        dominio = obj.domains.filter(is_primary=True).first()
        if dominio:
            url = f"http://{dominio.domain}"
            return format_html('<a href="{}" target="_blank" class="button" style="background: #6366f1; padding: 2px 8px; font-size: 9px; color: white; border-radius: 4px;">Abrir Portal</a>', url)
        return "-"

    @admin.display(description='Subdominio')
    def display_subdominio(self, obj):
        return format_html('<code>{}.localhost</code>', obj.schema_name)

    def get_plan_badge(self, obj):
        colors = {'basico': '#3b82f6', 'pro': '#8b5cf6'}
        color = colors.get(obj.plan.lower(), '#6b7280')
        return format_html('<span style="background: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>', color, obj.plan)

    def extender_trial_7_dias(self, request, queryset):
        for clinica in queryset:
            clinica.trial_end_date += timedelta(days=7)
            clinica.save()
        self.message_user(request, "Se han extendido 7 días.")
    extender_trial_7_dias.short_description = "⏳ Extender Trial +7 días"

    def suspender_clinica(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Clínicas suspendidas.")
    suspender_clinica.short_description = "⛔ Suspender Clínica"

@admin.register(Dominio)
class DominioAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant_link', 'is_primary')
    list_select_related = ('tenant',)
    list_filter = ('is_primary',)
    search_fields = ('domain', 'tenant__nombre_clinica')

    @admin.display(description='Clínica')
    def tenant_link(self, obj):
        url = reverse('admin:clientes_clinica_change', args=[obj.tenant.pk])
        return format_html('<a href="{}" style="font-weight: bold; color: #4f46e5;">{}</a>', url, obj.tenant.nombre_clinica)

    def save_model(self, request, obj, form, change):
        if obj.is_primary:
            Dominio.objects.filter(tenant=obj.tenant, is_primary=True).exclude(pk=obj.pk).update(is_primary=False)
        super().save_model(request, obj, form, change)

@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('clinica', 'get_pago_status', 'plan_tipo', 'metodo_pago', 'fecha_vencimiento', 'preview', 'fast_actions')
    list_editable = ('metodo_pago',)
    list_filter = (ExpiracionFiltro, 'estado_pago', 'plan_tipo', 'metodo_pago')
    search_fields = ('clinica__nombre_clinica', 'clinica__schema_name', 'external_reference')
    readonly_fields = ('preview_large',)
    actions = ['aprobar_pago_manual', 'regalar_cortesia']

    @admin.display(description='Aprobar/Rechazar')
    def fast_actions(self, obj):
        if obj.estado_pago == 'VALIDACION':
            approve_url = reverse('admin:approve_sub', args=[obj.pk])
            reject_url = reverse('admin:reject_sub', args=[obj.pk])
            return format_html(
                '<a href="{}" title="Aprobar" style="color: #10b981; font-size: 1.2rem; margin-right: 10px;">✅</a>'
                '<a href="{}" title="Rechazar" style="color: #ef4444; font-size: 1.2rem;">❌</a>',
                approve_url, reject_url
            )
        return "-"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('approve/<int:sub_id>/', self.admin_site.admin_view(self.approve_sub_view), name='approve_sub'),
            path('reject/<int:sub_id>/', self.admin_site.admin_view(self.reject_sub_view), name='reject_sub'),
        ]
        return custom_urls + urls

    def approve_sub_view(self, request, sub_id):
        sub = self.get_object(request, sub_id)
        if sub:
            sub.estado_pago = 'APROBADO'
            sub.fecha_vencimiento = timezone.now() + timedelta(days=30)
            sub.save()
            c = sub.clinica
            c.is_trial = False
            c.trial_end_date = sub.fecha_vencimiento
            c.save()
            self.message_user(request, f"Suscripción de {c.nombre_clinica} aprobada.")
        return redirect(reverse('admin:clientes_suscripcion_changelist'))

    def reject_sub_view(self, request, sub_id):
        sub = self.get_object(request, sub_id)
        if sub:
            sub.estado_pago = 'RECHAZADO'
            sub.save()
            self.message_user(request, f"Suscripción de {sub.clinica.nombre_clinica} rechazada.", level='warning')
        return redirect(reverse('admin:clientes_suscripcion_changelist'))

    def regalar_cortesia(self, request, queryset):
        for sub in queryset:
            vencimiento = timezone.now() + timedelta(days=30)
            sub.estado_pago = 'CORTESIA'
            sub.metodo_pago = 'CORTESIA'
            sub.fecha_vencimiento = vencimiento
            sub.save()
            
            c = sub.clinica
            c.is_trial = False
            c.trial_end_date = vencimiento
            c.save()
        self.message_user(request, "Meses de cortesía activados correctamente.")
    regalar_cortesia.short_description = "🎁 Regalar 30 días de Cortesía"

    def save_model(self, request, obj, form, change):
        if 'estado_pago' in form.changed_data and obj.estado_pago in ['APROBADO', 'CORTESIA']:
            if not obj.fecha_vencimiento:
                obj.fecha_vencimiento = timezone.now() + timedelta(days=30)
            obj.notas_admin = f"Aprobado por {request.user.username}"
            obj.save()
            clinica = obj.clinica
            clinica.is_trial = False
            clinica.trial_end_date = obj.fecha_vencimiento
            clinica.save()
        super().save_model(request, obj, form, change)

    def aprobar_pago_manual(self, request, queryset):
        for sub in queryset:
            sub.estado_pago = 'APROBADO'
            sub.fecha_vencimiento = timezone.now() + timedelta(days=30)
            sub.save()
            c = sub.clinica
            c.is_trial = False
            c.trial_end_date = sub.fecha_vencimiento
            c.save()
        self.message_user(request, "Suscripciones activadas.")

    def preview(self, obj):
        if obj.comprobante_img:
            return format_html('<a href="{}" target="_blank"><img src="{}" style="width: 35px; height: 35px; border-radius: 6px;" /></a>', obj.comprobante_img.url, obj.comprobante_img.url)
        return "N/A"

    def preview_large(self, obj):
        if obj.comprobante_img:
            return format_html('<img src="{}" style="max-width: 100%; border-radius: 8px;" />', obj.comprobante_img.url)
        return "Sin comprobante."

    def get_pago_status(self, obj):
        colors = {'APROBADO': '#dcfce7', 'VALIDACION': '#fef9c3', 'RECHAZADO': '#fee2e2'}
        text = {'APROBADO': '#166534', 'VALIDACION': '#854d0e', 'RECHAZADO': '#991b1b'}
        return format_html('<span style="background:{}; color:{}; padding: 3px 8px; border-radius: 5px; font-weight:bold; font-size:10px;">{}</span>', colors.get(obj.estado_pago, '#f3f4f6'), text.get(obj.estado_pago, '#374151'), obj.estado_pago)
