"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from clientes import views

urlpatterns = [
    path('plan-expirado/', views.plan_expirado, name='plan_expirado'),
    path('facturacion/', include([
        path('', views.facturacion_planes, name='facturacion_planes'),
        path('checkout/', views.checkout_2checkout, name='checkout_2checkout'),
        path('comprobante/', views.subir_comprobante, name='subir_comprobante'),
    ])),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('gestion.urls')),
]

# Esto permite ver las imágenes en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
