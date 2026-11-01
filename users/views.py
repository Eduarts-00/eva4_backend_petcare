"""
Vistas de autenticación híbrida (Sesiones de Django + Tokens JWT), control de bloqueo
de cuentas y cambio obligatorio de contraseña inicial para nuevos médicos contratados.
"""
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import CustomUser
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    CambiarPasswordSeguraSerializer,
    RegistroUsuarioSerializer,
)


class CustomLoginView(TokenObtainPairView):
    """
    Inicia sesión generando tanto la Sesión de Servidor de Django (cookie sessionid)
    como el par de tokens JWT (access y refresh), verificando primero si la cuenta fue
    bloqueada o inhabilitada por Administración.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''

        # Detectar cuentas bloqueadas/inhabilitadas por Administración (protección o despido)
        candidato = CustomUser.objects.filter(username=username).first()
        if candidato and not candidato.is_active and candidato.check_password(password):
            return Response(
                {
                    'detalle': (
                        '⛔ Acceso denegado: Esta cuenta ha sido bloqueada o inhabilitada '
                        'por Administración (protección de seguridad o desvinculación laboral).'
                    ),
                    'cuenta_bloqueada': True,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user = authenticate(request, username=username, password=password)
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200 and user is not None:
            login(request, user)
        return response


class LogoutSessionView(APIView):
    """Cierra la sesión activa de Django de forma segura."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logout(request)
        return Response({'detalle': 'Sesión cerrada correctamente.'}, status=status.HTTP_200_OK)


class PerfilActualView(APIView):
    """Retorna la información y rol del usuario autenticado actualmente, manteniendo sincronizada la sesión Django."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_active:
            logout(request)
            return Response({'detalle': 'Cuenta inhabilitada.'}, status=status.HTTP_403_FORBIDDEN)
        if '_auth_user_id' not in request.session:
            login(request, request.user, backend='django.contrib.auth.backends.ModelBackend')
        return Response(UserProfileSerializer(request.user).data)


class CambiarPasswordView(APIView):
    """
    Permite al médico recién contratado (o cualquier usuario autenticado) actualizar
    su contraseña temporal por una nueva y segura, liberando el bloqueo de primer ingreso.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CambiarPasswordSeguraSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['password_nueva'])
        user.debe_cambiar_password = False
        user.save(update_fields=['password', 'debe_cambiar_password'])

        # Mantener viva la sesión de servidor con el nuevo hash de contraseña
        update_session_auth_hash(request, user)

        return Response(
            {
                'detalle': 'Contraseña actualizada exitosamente. Acceso clínico habilitado.',
                'user': UserProfileSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class RegistroUsuarioView(generics.CreateAPIView):
    """Permite el registro de nuevas cuentas de Tutor en el portal PetCare."""
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegistroUsuarioSerializer
