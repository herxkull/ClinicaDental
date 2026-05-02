from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from clientes import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('registro/', views.registro_clinica, name='registro_clinica'),
    path('google/login/', views.google_init, name='google_login'),
    path('google/init/', views.google_init, name='google_init'),
    path('google/callback/', views.google_callback, name='google_callback'),
    path('finalizar-registro/', views.finalizar_registro_google, name='finalizar_registro_google'),
    path('api/check-subdomain/', views.check_subdomain, name='check_subdomain'),
    path('2checkout/ipn/', views.ipn_2checkout, name='ipn_2checkout'),
    path('admin/pagos/', views.admin_pagos_pendientes, name='admin_pagos_pendientes'),
    path('admin/pagos/aprobar/<int:sub_id>/', views.aprobar_pago_manual, name='aprobar_pago_manual'),
    path('acceso/', views.acceso_doctor, name='acceso_doctor'),
    path('', views.home_publico, name='home_publico'), # La raíz del SaaS
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)