"""Rutas de autenticación, cambio seguro de contraseña, sesiones y verificación criptográfica (EVA 4)."""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomLoginView,
    LogoutSessionView,
    PerfilActualView,
    CambiarPasswordView,
    RegistroUsuarioView,
    VerificarCriptografiaPasswordView,
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='auth-login'),
    path('logout/', LogoutSessionView.as_view(), name='auth-logout'),
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('perfil/', PerfilActualView.as_view(), name='auth-perfil'),
    path('cambiar-password/', CambiarPasswordView.as_view(), name='auth-cambiar-password'),
    path('registro/', RegistroUsuarioView.as_view(), name='auth-registro'),
    path('verificar-hash/', VerificarCriptografiaPasswordView.as_view(), name='auth-verificar-hash'),
]
