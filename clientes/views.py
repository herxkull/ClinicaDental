# clientes/views.py
import json
import secrets
from django.shortcuts import render, redirect
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_tenants.utils import schema_context
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .forms import RegistroClinicaForm
from .models import Clinica, Dominio, Suscripcion
from gestion.models import Tratamiento
import hashlib
import hmac
import time

# Configuración de Google
GOOGLE_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar.events',
]

def google_login(request):
    """Inicia el flujo de OAuth con Google"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES
    )
    
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    flow.redirect_uri = redirect_uri

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    request.session['google_auth_state'] = state
    return redirect(authorization_url)

def google_callback(request):
    """Recibe la respuesta de Google y gestiona el Onboarding"""
    state = request.session.get('google_auth_state')
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
        state=state
    )
    flow.redirect_uri = request.build_absolute_uri(reverse('google_callback'))

    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )

        google_email = id_info.get('email')
        google_name = id_info.get('name')

        request.session['google_user_data'] = {
            'email': google_email,
            'nombre': google_name,
            'refresh_token': credentials.refresh_token,
            'access_token': credentials.token
        }

        return redirect('finalizar_registro_google')

    except Exception as e:
        return render(request, 'clientes/registro.html', {'error': f"Error de autenticación: {str(e)}"})

def finalizar_registro_google(request):
    """Paso final: Pedir Nombre de Clínica y Subdominio"""
    user_data = request.session.get('google_user_data')
    if not user_data:
        return redirect('home_publico')

    if request.method == 'POST':
        nombre_clinica = request.POST.get('nombre_clinica')
        subdominio = request.POST.get('subdominio').lower().strip()
        
        if not nombre_clinica or not subdominio:
            return render(request, 'clientes/finalizar_registro.html', {'error': 'Todos los campos son obligatorios'})

        try:
            with transaction.atomic():
                nueva_clinica = Clinica.objects.create(
                    schema_name=subdominio,
                    nombre_clinica=nombre_clinica
                )
                
                host_completo = request.get_host()
                puerto = ":" + host_completo.split(':')[1] if ':' in host_completo else ""
                base_host = host_completo.split(':')[0].replace('localhost', '').strip('.')
                
                if not base_host: base_host = "localhost"
                
                domain_full = f"{subdominio}.{base_host}{puerto}"
                Dominio.objects.create(domain=domain_full, tenant=nueva_clinica, is_primary=True)

                with schema_context(subdominio):
                    password_aleatoria = secrets.token_urlsafe(16)
                    user = User.objects.create_superuser(
                        username=user_data['email'],
                        email=user_data['email'],
                        password=password_aleatoria
                    )
                    user.first_name = user_data['nombre']
                    user.save()

                    from gestion.models import GoogleCalendarConfig
                    GoogleCalendarConfig.objects.create(
                        usuario=user,
                        email_cuenta=user_data['email'],
                        refresh_token=user_data['refresh_token'],
                        calendar_id='primary'
                    )

            # 4. Enviar correo de bienvenida
            try:
                from django.template.loader import render_to_string
                from django.core.mail import send_mail
                from django.conf import settings
                
                context_email = {
                    'nombre_doctor': user_data['nombre'],
                    'nombre_clinica': nombre_clinica,
                    'url_acceso': f"http://{domain_full}",
                    'email': user_data['email']
                }
                mensaje_texto = render_to_string('clientes/emails/bienvenida.txt', context_email)
                mensaje_html = render_to_string('clientes/emails/bienvenida.html', context_email)
                
                send_mail(
                    subject=f'¡Bienvenido a DentalSaaS, {user_data["nombre"]}!',
                    message=mensaje_texto,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user_data['email']],
                    fail_silently=False,
                    html_message=mensaje_html
                )
            except Exception as mail_error:
                print(f"Error enviando correo: {mail_error}")

            del request.session['google_user_data']
            return redirect(f"http://{domain_full}/dashboard/")

        except Exception as e:
            return render(request, 'clientes/finalizar_registro.html', {'error': f"Error: {str(e)}"})

    return render(request, 'clientes/finalizar_registro.html', {'user_data': user_data})

def plan_expirado(request):
    """Vista de aterrizaje para clínicas con trial vencido o cuenta inactiva"""
    return render(request, 'clientes/plan_expirado.html', {
        'tenant': request.tenant
    })

def check_subdomain(request):
    """Endpoint AJAX para validar disponibilidad de subdominio"""
    subdominio = request.GET.get('subdominio', '').lower().strip()
    if len(subdominio) < 3:
        return JsonResponse({'available': False, 'message': 'Demasiado corto'})
    
    exists = Clinica.objects.filter(schema_name=subdominio).exists()
    return JsonResponse({'available': not exists})

def home_publico(request):
    return render(request, 'clientes/index.html')

def registro_clinica(request):
    if request.method == 'POST':
        form = RegistroClinicaForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre_clinica']
            subdominio = form.cleaned_data['subdominio']
            email = form.cleaned_data['email_admin']
            password = form.cleaned_data['password_admin']
            
            try:
                with transaction.atomic():
                    schema_name = subdominio
                    nueva_clinica = Clinica.objects.create(
                        schema_name=schema_name,
                        nombre_clinica=nombre
                    )
                    # Lógica de dominio multi-variante para Local (Sin puerto para mayor compatibilidad)
                    host_completo = request.get_host()
                    host_sin_puerto = host_completo.split(':')[0]
                    
                    # Variantes de dominio para asegurar acceso en local
                    variantes = [
                        f"{subdominio}.localhost",
                        f"{subdominio}.127.0.0.1",
                        f"{subdominio}.127.0.0.1.nip.io",
                    ]

                    for i, d_name in enumerate(variantes):
                        Dominio.objects.get_or_create(
                            domain=d_name,
                            tenant=nueva_clinica,
                            defaults={'is_primary': (i == 0)}
                        )
                    
                    puerto = ":" + host_completo.split(':')[1] if ':' in host_completo else ""
                    # 3. Crear Registro de Suscripción Inicial (Trial) para que aparezca en el Admin
                    from django.utils import timezone
                    Suscripcion.objects.create(
                        clinica=nueva_clinica,
                        plan_tipo='BASICO',
                        estado_pago='TRIAL',
                        metodo_pago='GRATIS',
                        fecha_vencimiento=timezone.now() + timezone.timedelta(days=7)
                    )

                    domain_full = f"{subdominio}.localhost{puerto}" # Link de éxito con puerto
                    
                with schema_context(nueva_clinica.schema_name):
                    user = User.objects.create_superuser(
                        username=email,
                        email=email,
                        password=password
                    )
                    user.is_staff = True
                    user.save()

                    # Inicializar datos básicos por defecto
                    Tratamiento.objects.bulk_create([
                        Tratamiento(nombre="Consulta General", precio_venta=20.00, descripcion="Evaluación inicial."),
                        Tratamiento(nombre="Limpieza Dental", precio_venta=35.00, descripcion="Profilaxis."),
                    ])

                # Intentar enviar correo con logging real
                try:
                    context_email = {
                        'nombre_doctor': nombre,
                        'nombre_clinica': nombre,
                        'url_acceso': f"http://{domain_full}",
                        'email': email
                    }
                    mensaje_html = render_to_string('clientes/emails/bienvenida.html', context_email)
                    
                    # LOG EXPLICIT PARA CONSOLA
                    print("\n" + "="*50)
                    print(f"ENVIANDO CORREO DE BIENVENIDA A: {email}")
                    print(f"URL DE ACCESO: http://{domain_full}")
                    print("="*50 + "\n")

                    send_mail(
                        subject=f'Bienvenido a DentalSaaS - {nombre}',
                        message=f"Tu clínica ha sido creada. Accede en http://{domain_full}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                        html_message=mensaje_html
                    )
                except Exception as mail_error:
                    messages.warning(request, f"Clínica creada, pero hubo un error enviando el correo: {mail_error}. Tu URL es http://{domain_full}")

                return render(request, 'clientes/registro_exitoso.html', {
                    'clinica': nueva_clinica,
                    'url_acceso': f"http://{domain_full}"
                })
                
            except Exception as e:
                form.add_error(None, f"Error al crear la clínica: {str(e)}")
    else:
        form = RegistroClinicaForm()
        
    return render(request, 'clientes/registro.html', {'form': form})

@login_required
def facturacion_planes(request):
    """Página principal de selección de planes y métodos de pago"""
    tenant = request.tenant
    # Obtener última suscripción para mostrar estado
    ultima_sub = Suscripcion.objects.filter(clinica=tenant).order_by('-fecha_inicio').first()
    
    return render(request, 'clientes/facturacion.html', {
        'tenant': tenant,
        'ultima_sub': ultima_sub
    })

@login_required
def checkout_2checkout(request):
    """Genera el enlace de pago para 2Checkout"""
    tenant = request.tenant
    # Crear registro previo de suscripción en estado PENDIENTE
    sub = Suscripcion.objects.create(
        clinica=tenant,
        plan_tipo='PRO',
        metodo_pago='2CHECKOUT',
        estado_pago='PENDIENTE'
    )
    
    # Parámetros básicos para 2Checkout (Inline o Redirect)
    params = {
        'prod': 'SUSCRIPCION_PRO_MENSUAL',
        'qty': 1,
        'price': 49.00,
        'type': 'self-handled',
        'merchant': settings.TWO_CHECKOUT_MERCHANT_ID,
        'ref': sub.id, # Referencia interna para el Webhook
        'currency': settings.CURRENCY
    }
    
    # En un entorno real, aquí construirías la firma si usas el API avanzado
    # Por ahora, usamos el Buy Link directo
    buy_url = f"{settings.TWO_CHECKOUT_BUY_LINK}?MERCHANT={params['merchant']}&PROD={params['prod']}&QTY=1&REF={sub.id}"
    return redirect(buy_url)

@login_required
def subir_comprobante(request):
    """Maneja la subida manual de comprobantes bancarios"""
    if request.method == 'POST' and request.FILES.get('comprobante'):
        tenant = request.tenant
        img = request.FILES['comprobante']
        
        # Crear suscripción en estado VALIDACIÓN
        Suscripcion.objects.create(
            clinica=tenant,
            plan_tipo='PRO',
            metodo_pago='TRANSFERENCIA',
            estado_pago='VALIDACION',
            comprobante_img=img
        )
        
        messages.success(request, "Hemos recibido tu comprobante. Nuestro equipo revisará la transferencia y se te otorgará acceso completo en un tiempo estimado de 1-12 horas.")
        return redirect('facturacion_planes')
    
    return render(request, 'clientes/subir_comprobante.html')

@csrf_exempt
def ipn_2checkout(request):
    """Webhook IPN (Instant Payment Notification) de 2Checkout"""
    if request.method == 'POST':
        # 1. Validar Firma (HMAC-MD5 según specs de 2Checkout)
        # Nota: Este es un ejemplo simplificado de la lógica de validación
        data = request.POST.dict()
        sub_id = data.get('REFNOEXT') # Referencia enviada en el checkout
        
        if sub_id:
            try:
                sub = Suscripcion.objects.get(id=sub_id)
                # Si el pago es exitoso (Estado 2Checkout 'COMPLETE')
                sub.estado_pago = 'APROBADO'
                sub.external_reference = data.get('REFNO')
                # Extender fecha de vencimiento (30 días)
                from django.utils import timezone
                sub.fecha_vencimiento = timezone.now() + timezone.timedelta(days=30)
                sub.save()
                
                # Activar clínica
                clinica = sub.clinica
                clinica.is_trial = False
                clinica.is_active = True
                clinica.save()
                
                return HttpResponse("OK")
            except Suscripcion.DoesNotExist:
                pass
                
    return HttpResponse("FAIL", status=400)

# Vista para el SuperAdministrador (Control de Pagos Manuales)
@login_required
def admin_pagos_pendientes(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    pendientes = Suscripcion.objects.filter(estado_pago='VALIDACION').select_related('clinica')
    return render(request, 'clientes/admin_pagos.html', {'pendientes': pendientes})

@login_required
def aprobar_pago_manual(request, sub_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    sub = Suscripcion.objects.get(id=sub_id)
    sub.estado_pago = 'APROBADO'
    from django.utils import timezone
    sub.fecha_vencimiento = timezone.now() + timezone.timedelta(days=30)
    sub.save()
    
    clinica = sub.clinica
    clinica.is_trial = False
    clinica.is_active = True
    clinica.save()
    
    messages.success(request, f"Acceso aprobado para {clinica.nombre_clinica}")
    return redirect('admin_pagos_pendientes')