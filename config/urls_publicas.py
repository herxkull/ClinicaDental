# config/urls_publicas.py
from django.contrib import admin
from django.urls import path
from clientes.views import home_publico, registro_clinica

urlpatterns = [
    path('admin/', admin.site.urls),
    path('registro/', registro_clinica, name='registro_clinica'),
    path('', home_publico, name='home_publico'), # La raíz del SaaS
]