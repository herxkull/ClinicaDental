from django import template

register = template.Library()

@register.filter(name='tiene_grupo')
def tiene_grupo(user, group_name):
    """Devuelve True si el usuario pertenece al grupo o es superusuario"""
    if user.is_superuser:
        return True
    return user.groups.filter(name=group_name).exists()