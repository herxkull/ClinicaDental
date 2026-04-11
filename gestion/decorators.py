from django.http import HttpResponseForbidden


def grupo_requerido(*nombres_grupos):
    """
    Decorador que verifica si el usuario pertenece a uno de los grupos permitidos
    o si es un superusuario (admin).
    """

    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            # Si el usuario es superusuario, lo dejamos pasar siempre
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Verificamos si pertenece a alguno de los grupos requeridos
            if request.user.groups.filter(name__in=nombres_grupos).exists():
                return view_func(request, *args, **kwargs)

            # Si no es admin ni tiene el grupo, le bloqueamos el paso
            return HttpResponseForbidden(
                "<h1>Acceso Denegado</h1> <p>No tienes los permisos necesarios para realizar esta acción.</p>")

        return wrapper_func

    return decorator