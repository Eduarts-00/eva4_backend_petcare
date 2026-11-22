"""
Middlewares de seguridad (OWASP ZAP DAST Hardening), soporte CORS para
Arquitectura Distribuida AWS (EC2 Frontend + API Gateway + EC2 Backend DRF)
y enrutamiento seguro para PetCare (Evaluación N.º 4).
"""
from django.http import HttpResponse
from django.shortcuts import redirect


class SecurityHeadersAndCORSMiddleware:
    """
    1. Normaliza rutas /api/... provenientes de Amazon API Gateway ({proxy+} remueve el slash final)
       para evitar redirecciones 301/302 fuera del stage /prod de API Gateway.
    2. Aplica cabeceras de seguridad HTTP recomendadas por OWASP ZAP (DAST):
       - Content-Security-Policy (CSP)
       - X-Content-Type-Options: nosniff
       - X-Frame-Options: DENY
       - Referrer-Policy: strict-origin-when-cross-origin
       - Permissions-Policy
       - Cache-Control restrictivo en endpoints de autenticación JWT
    3. Habilita CORS para permitir la integración desacoplada entre EC2 Frontend (3.230.130.63),
       Amazon API Gateway (ozp0ipskkf.execute-api.us-east-1.amazonaws.com/prod) y EC2 Backend DRF.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Normalizar slash final cuando Amazon API Gateway reenvía /{proxy} sin '/' al final
        if request.path.startswith('/api/') and not request.path.endswith('/'):
            request.path = request.path + '/'
            request.path_info = request.path_info + '/'

        origin = request.headers.get('Origin', '*')

        if request.method == 'OPTIONS' and request.path.startswith('/api/'):
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        # Cabeceras CORS para integración EC2 Frontend <-> API Gateway <-> EC2 Backend
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = origin if origin != 'null' else '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Authorization, Content-Type, X-CSRFToken, X-Requested-With'
            )
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'

        # Cabeceras de endurecimiento DAST (OWASP ZAP Baseline Compliance)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=()'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'

        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = (
                "default-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "font-src 'self' https://cdn.jsdelivr.net data:; "
                "img-src 'self' data: https: blob:; "
                "connect-src 'self' https: http:; "
                "frame-ancestors 'none';"
            )

        if request.path.startswith('/api/auth/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'

        return response


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
