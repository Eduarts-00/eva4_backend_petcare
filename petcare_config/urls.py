"""
Enrutamiento principal del proyecto PetCare con Inicio de Sesión Unificado por Rango.
Alumno: Angel Eduardo Lara Manriquez
Sección: IEC-N4-C2
Docente: Marcelo Alvarado Aravena
Año: 2026
"""
from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path, re_path, include
from django.views.generic import TemplateView, RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def admin_logout_unificado(request):
    """Cierra la sesión de Django Admin y sincroniza el cierre en el portal unificado."""
    logout(request)
    return redirect('/?logged_out=1')


def redirigir_a_inicio(request, exception=None):
    """Manejador global 404 para enviar cualquier ruta desconocida al inicio."""
    return redirect('/')


# Personalización de títulos globales del Administrador de Django (Criterio 2)
admin.site.site_header = "🐾 PetCare — Administración Clínica Veterinaria"
admin.site.site_title = "PetCare Admin"
admin.site.index_title = "Panel de Gestión de Pacientes, Agenda Médica, Fichas y Vacunación"

urlpatterns = [
    # Portal principal informativo con Login Unificado y vistas dinámicas según Rango
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    # Unificar el login y logout de /admin/ con el Login único del portal principal
    path('admin/login/', RedirectView.as_view(url='/', query_string=True)),
    path('admin/logout/', admin_logout_unificado),
    path('admin/', admin.site.urls),

    # Endpoints de Autenticación Híbrida (Sesión Django + JWT) y Roles
    path('api/auth/', include('users.urls')),

    # Endpoints CRUD y Reglas de Negocio Clínica Veterinaria PetCare
    path('api/', include('clinica.urls')),

    # Documentación interactiva OpenAPI / Swagger / Redoc
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Catch-all: cualquier otra ruta escrita en el navegador redirige automáticamente al inicio
    re_path(r'^(?!api/|static/|media/).*$', RedirectView.as_view(url='/', permanent=False)),
]

handler404 = 'petcare_config.urls.redirigir_a_inicio'
