"""
Vistas de autenticación híbrida (Sesiones de Django + Tokens JWT), control de bloqueo
de cuentas, cambio obligatorio de contraseña inicial y demostración práctica de
Criptografía y Hashing de Contraseñas (Actividad 3 - Evaluación N.º 4).
"""
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import identify_hasher, make_password, check_password
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


class VerificarCriptografiaPasswordView(APIView):
    """
    Actividad 3 (Evaluación N.º 4): Evidencia práctica de protección de contraseñas y criptografía.
    Demuestra que las contraseñas en PostgreSQL (tabla users_customuser) jamás se almacenan
    en texto plano, desglosando el algoritmo PBKDF2-HMAC-SHA256, el factor de trabajo (iteraciones),
    el salt criptográfico único por registro y el digest derivado en Base64.
    """
    permission_classes = [permissions.AllowAny]

    def _desglosar_hash_django(self, encoded_hash: str) -> dict:
        partes = encoded_hash.split('$')
        algoritmo = partes[0] if len(partes) > 0 else 'desconocido'
        iteraciones = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else None
        salt = partes[2] if len(partes) > 2 else ''
        digest = partes[3] if len(partes) > 3 else ''
        hasher = identify_hasher(encoded_hash)
        resumenseguro = hasher.safe_summary(encoded_hash)
        return {
            'formato_estructural': '<algoritmo>$<iteraciones>$<salt>$<hash_base64>',
            'algoritmo': algoritmo,
            'clase_hasher_django': f"{hasher.__class__.__module__}.{hasher.__class__.__name__}",
            'funcion_prf': 'HMAC-SHA256 (Familia SHA-2 de 256 bits)',
            'iteraciones': iteraciones,
            'salt': salt,
            'longitud_salt_chars': len(salt),
            'digest_base64': digest,
            'longitud_digest_bits': 256,
            'hash_completo_bd': encoded_hash,
            'resumen_seguro_django': {str(k): str(v) for k, v in resumenseguro.items()},
        }

    def get(self, request):
        sample_password = request.query_params.get('password_demo', 'PetCareSegura2026!')
        if request.user and request.user.is_authenticated:
            target_user = request.user
        else:
            target_user = CustomUser.objects.order_by('id').first()

        # Demostración de que dos hashes de la misma contraseña producen salidas distintas por el Salt único
        hash_demo_1 = make_password(sample_password)
        hash_demo_2 = make_password(sample_password)

        datos_usuario_bd = None
        if target_user and target_user.password:
            desglose_bd = self._desglosar_hash_django(target_user.password)
            datos_usuario_bd = {
                'username': target_user.username,
                'rol': target_user.rol,
                'tabla_postgresql': CustomUser._meta.db_table,
                'almacenado_en_texto_plano': False,
                'desglose_criptografico': desglose_bd,
            }

        return Response({
            'actividad': 'Actividad 3 — Protección de contraseñas y criptografía (PBKDF2 / Argon2)',
            'hashers_configurados_settings': settings.PASSWORD_HASHERS,
            'validador_longitud_minima': 8,
            'registro_real_postgresql': datos_usuario_bd,
            'demostracion_salt_unico': {
                'explicacion': (
                    'Al aplicar make_password() dos veces sobre la misma contraseña, Django genera '
                    'un salt aleatorio criptográficamente seguro de 128 bits en cada invocación, '
                    'produciendo digests completamente diferentes e invalidando ataques con Rainbow Tables.'
                ),
                'hash_ejecucion_1': self._desglosar_hash_django(hash_demo_1),
                'hash_ejecucion_2': self._desglosar_hash_django(hash_demo_2),
                'hashes_identicos': hash_demo_1 == hash_demo_2,
                'verificacion_check_password_1': check_password(sample_password, hash_demo_1),
                'verificacion_check_password_2': check_password(sample_password, hash_demo_2),
            },
        })
