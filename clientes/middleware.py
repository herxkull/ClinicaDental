from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from .models import Suscripcion

class TrialExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = getattr(request, 'tenant', None)

        if not tenant or tenant.schema_name == 'public':
            return self.get_response(request)

        # Rutas permitidas durante el proceso de pago
        exempt_urls = [
            reverse('plan_expirado'), 
            reverse('facturacion_planes'),
            reverse('subir_comprobante'),
            reverse('checkout_2checkout'),
            '/admin/', '/static/', '/media/', '/logout/', '/accounts/'
        ]
        
        path = request.path
        if any(path.startswith(url) for url in exempt_urls):
            return self.get_response(request)

        # 1. Bloqueo si is_active es False (para suspensiones manuales)
        if not tenant.is_active:
            return redirect('plan_expirado')

        # 2. Bloqueo si hay una suscripción RECHAZADA activa
        if Suscripcion.objects.filter(clinica=tenant, estado_pago='RECHAZADO').exists():
            return redirect('plan_expirado')

        # 3. Lógica de Trial Expirado
        if tenant.is_trial:
            if tenant.trial_expirado:
                # Si el trial expiró y no hay nada en validación, bloquear
                if not Suscripcion.objects.filter(clinica=tenant, estado_pago='VALIDACION').exists():
                    return redirect('plan_expirado')

        return self.get_response(request)
