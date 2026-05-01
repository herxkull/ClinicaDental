import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from django.db.models import Sum, F
from django.utils import timezone
from gestion.models import Pago

with schema_context('pelusmi'):
    hoy = timezone.localtime(timezone.now()).date()
    primer_dia_mes = hoy.replace(day=1)
    seis_meses_atras = primer_dia_mes - timezone.timedelta(days=150)
    print(f"Buscando pagos desde: {seis_meses_atras}")
    
    pagos = Pago.objects.filter(fecha__date__gte=seis_meses_atras)
    print(f"Total pagos encontrados en el rango: {pagos.count()}")
    
    for p in pagos:
        print(f"Pago id: {p.id}, Monto: {p.monto}, Fecha: {p.fecha}")
        
    ingresos_qs = pagos.annotate(
        mes=F('fecha__month'),
        anio=F('fecha__year')
    ).values('mes', 'anio').annotate(total=Sum('monto')).order_by('anio', 'mes')
    print("Resultado ingresos_qs:", list(ingresos_qs))
