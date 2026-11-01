"""
Middleware de enrutamiento seguro para PetCare.
Redirige cualquier URL web inexistente (404 fuera de /api/ y /static/) hacia la portada principal ('/'),
evitando exponer rutas internas o pantallas de error al usuario final.
"""
from django.shortcuts import redirect


class RedirectUnknownRoutesMiddleware:
    """Redirige rutas desconocidas al Inicio ('/') conservando intactas las respuestas JSON de /api/."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            response.status_code == 404
            and not request.path.startswith(('/api/', '/static/', '/media/'))
        ):
            return redirect('/')
        return response
