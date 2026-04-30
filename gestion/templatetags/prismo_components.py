from django import template

register = template.Library()

@register.inclusion_tag('gestion/components/kpi_card.html')
def kpi_card(title, value, icon, color='blue', trend=None):
    """Componente para tarjetas de indicadores (KPIs)"""
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'color': color,
        'trend': trend
    }

@register.inclusion_tag('gestion/components/status_badge.html')
def status_badge(status):
    """Componente para badges de estado (Citas, Pagos)"""
    config = {
        'PENDIENTE': {'color': 'orange', 'label': 'Pendiente'},
        'COMPLETADA': {'color': 'green', 'label': 'Completada'},
        'CANCELADA': {'color': 'red', 'label': 'Cancelada'},
        'CONFIRMADA': {'color': 'blue', 'label': 'Confirmada'},
    }
    return config.get(status.upper(), {'color': 'gray', 'label': status})
