"""
Vistas y Controladores REST (ViewSets) para PetCare (Criterio 3 y Criterio 4).
Implementa:
- CRUD de Tutores y Mascotas.
- Agendamiento de Citas con cálculo de bloques de disponibilidad por profesional y transacción atómica.
- Gestión de Fichas Clínicas Digitales.
- Seguimiento y alertas de Vacunación y Controles Periódicos.
"""
from datetime import datetime, timedelta
from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import CustomUser
from users.permissions import (
    IsAdminOrReadOnlyAuthenticated,
    IsStaffClinicoOrReadOnly,
    IsVeterinarioOrAdmin,
)
from .models import Profesional, Tutor, Mascota, CitaMedica, FichaClinica, ControlVacuna
from .serializers import (
    ProfesionalSerializer,
    TutorSerializer,
    MascotaSerializer,
    CitaMedicaSerializer,
    FichaClinicaSerializer,
    ControlVacunaSerializer,
)


class ProfesionalViewSet(viewsets.ModelViewSet):
    """
    CRUD de Médicos Veterinarios (exclusivo ADMIN), creación/bloqueo de cuentas clínicas
    y consulta en tiempo real de bloques disponibles.
    """
    queryset = Profesional.objects.select_related('usuario').all()
    serializer_class = ProfesionalSerializer
    permission_classes = [IsAdminOrReadOnlyAuthenticated]
    filterset_fields = ['especialidad', 'activo']
    search_fields = ['nombre_completo', 'rut', 'especialidad', 'usuario__username']

    @action(detail=True, methods=['post'])
    def cambiar_estado_cuenta(self, request, pk=None):
        """
        Permite al Administrador bloquear/inhabilitar (por protección o despido) o
        rehabilitar tanto la cuenta de usuario como la agenda médica del veterinario.
        """
        profesional = self.get_object()
        if 'activo' in request.data:
            nuevo_estado = bool(request.data.get('activo'))
        else:
            nuevo_estado = not profesional.activo

        with transaction.atomic():
            profesional.activo = nuevo_estado
            profesional.save(update_fields=['activo'])

            if profesional.usuario:
                profesional.usuario.is_active = nuevo_estado
                profesional.usuario.save(update_fields=['is_active'])

                # Si fue bloqueado/despedido, cerrar de inmediato cualquier sesión activa en el servidor
                if not nuevo_estado:
                    uid_str = str(profesional.usuario.pk)
                    for sesion in Session.objects.filter(expire_date__gte=timezone.now()):
                        if sesion.get_decoded().get('_auth_user_id') == uid_str:
                            sesion.delete()

        accion_txt = 'rehabilitada' if nuevo_estado else 'bloqueada e inhabilitada'
        return Response({
            'detalle': f"Cuenta y agenda del Dr(a). {profesional.nombre_completo} {accion_txt} correctamente.",
            'profesional': ProfesionalSerializer(profesional).data,
        })

    @action(detail=True, methods=['post'])
    def asignar_credenciales(self, request, pk=None):
        """
        Permite al Administrador crear una cuenta o asignar una nueva clave temporal a un médico,
        obligándolo a cambiar su contraseña por una segura en su próximo ingreso.
        """
        profesional = self.get_object()
        password_temporal = (request.data.get('password_temporal') or '').strip()
        username_req = (request.data.get('username') or '').strip()

        if len(password_temporal) < 6:
            return Response(
                {'error': 'La clave temporal debe tener al menos 6 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            if profesional.usuario:
                vet_user = profesional.usuario
                vet_user.set_password(password_temporal)
                vet_user.debe_cambiar_password = True
                vet_user.is_active = True
                vet_user.save(update_fields=['password', 'debe_cambiar_password', 'is_active'])
            else:
                if not username_req:
                    return Response(
                        {'error': 'Debes indicar un nombre de usuario para crear la cuenta del médico.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if CustomUser.objects.filter(username=username_req).exists():
                    return Response(
                        {'error': f"El usuario '{username_req}' ya existe."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                partes = profesional.nombre_completo.strip().split(' ', 1)
                vet_user = CustomUser(
                    username=username_req,
                    email=profesional.email,
                    first_name=partes[0] if partes else username_req,
                    last_name=partes[1] if len(partes) > 1 else '',
                    rol=CustomUser.Roles.VETERINARIO,
                    rut=profesional.rut,
                    telefono=profesional.telefono,
                    is_active=True,
                    debe_cambiar_password=True,
                )
                vet_user.set_password(password_temporal)
                vet_user.save()
                profesional.usuario = vet_user

            profesional.activo = True
            profesional.save(update_fields=['usuario', 'activo'])

        return Response({
            'detalle': f"Credenciales temporales listas para @{profesional.usuario.username}.",
            'profesional': ProfesionalSerializer(profesional).data,
        })

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def disponibilidad(self, request, pk=None):
        """
        Retorna todos los bloques horarios del veterinario para una fecha dada (?fecha=YYYY-MM-DD),
        indicando cuáles están disponibles y cuáles ocupados para evitar solapamientos.
        """
        profesional = self.get_object()
        fecha_str = request.query_params.get('fecha')
        if fecha_str:
            try:
                fecha_consulta = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            fecha_consulta = timezone.localdate()

        citas_ocupadas = list(
            CitaMedica.objects.filter(
                profesional=profesional,
                fecha=fecha_consulta,
                estado__in=[CitaMedica.Estados.PROGRAMADA, CitaMedica.Estados.CONFIRMADA, CitaMedica.Estados.ATENDIDA]
            ).select_related('mascota')
        )

        bloques = []
        actual = datetime.combine(fecha_consulta, profesional.hora_inicio_jornada)
        limite = datetime.combine(fecha_consulta, profesional.hora_fin_jornada)
        paso = timedelta(minutes=profesional.duracion_bloque_min or 30)

        while actual + paso <= limite:
            inicio_t = actual.time()
            fin_t = (actual + paso).time()
            cita_cruce = next(
                (c for c in citas_ocupadas if inicio_t < c.hora_fin and fin_t > c.hora_inicio),
                None
            )
            bloques.append({
                'hora_inicio': inicio_t.strftime('%H:%M'),
                'hora_fin': fin_t.strftime('%H:%M'),
                'disponible': cita_cruce is None,
                'paciente': cita_cruce.mascota.nombre if cita_cruce else None,
                'estado_cita': cita_cruce.get_estado_display() if cita_cruce else None,
            })
            actual += paso

        return Response({
            'profesional_id': profesional.id,
            'profesional': profesional.nombre_completo,
            'especialidad': profesional.get_especialidad_display(),
            'fecha': fecha_consulta.isoformat(),
            'bloques': bloques,
        })


class TutorViewSet(viewsets.ModelViewSet):
    """CRUD completo de Tutores (escritura exclusiva ADMIN; lectura Veterinarios y propio Tutor)."""
    queryset = Tutor.objects.prefetch_related('mascotas').all()
    serializer_class = TutorSerializer
    permission_classes = [IsAdminOrReadOnlyAuthenticated]
    search_fields = ['rut', 'nombres', 'apellidos', 'email', 'telefono']
    ordering_fields = ['apellidos', 'fecha_registro']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.rol == 'TUTOR' and not user.is_superuser:
            return qs.filter(usuario=user)
        return qs


class MascotaViewSet(viewsets.ModelViewSet):
    """CRUD completo de Mascotas vinculadas a Tutores."""
    queryset = Mascota.objects.select_related('tutor').all()
    serializer_class = MascotaSerializer
    permission_classes = [IsStaffClinicoOrReadOnly]
    filterset_fields = ['especie', 'sexo', 'tutor', 'esterilizado', 'activo']
    search_fields = ['nombre', 'raza', 'microchip', 'tutor__nombres', 'tutor__apellidos', 'tutor__rut']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.rol == 'TUTOR' and not user.is_superuser:
            return qs.filter(tutor__usuario=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.rol == 'TUTOR' and not user.is_superuser and hasattr(user, 'perfil_tutor'):
            serializer.save(tutor=user.perfil_tutor)
        else:
            serializer.save()


class CitaMedicaViewSet(viewsets.ModelViewSet):
    """
    Agendamiento de Citas Médicas con control transaccional atómico anti-solapamiento.
    Tanto el personal clínico como los Tutores autenticados pueden agendar citas.
    """
    queryset = CitaMedica.objects.select_related('mascota', 'mascota__tutor', 'profesional').all()
    serializer_class = CitaMedicaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['fecha', 'profesional', 'mascota', 'estado']
    search_fields = ['mascota__nombre', 'mascota__tutor__nombres', 'profesional__nombre_completo', 'motivo']
    ordering_fields = ['fecha', 'hora_inicio']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.rol == 'TUTOR' and not user.is_superuser:
            return qs.filter(mascota__tutor__usuario=user)
        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save()

    @action(detail=True, methods=['patch'])
    def cambiar_estado(self, request, pk=None):
        """Actualiza el estado de una cita (PROGRAMADA, CONFIRMADA, ATENDIDA, CANCELADA)."""
        cita = self.get_object()
        nuevo_estado = request.data.get('estado')
        if nuevo_estado not in dict(CitaMedica.Estados.choices):
            return Response({'error': 'Estado de cita no válido.'}, status=status.HTTP_400_BAD_REQUEST)
        cita.estado = nuevo_estado
        cita.save()
        return Response(CitaMedicaSerializer(cita).data)


class FichaClinicaViewSet(viewsets.ModelViewSet):
    """
    CRUD de Fichas Clínicas Digitales (diagnósticos, tratamientos, recetas y exámenes).
    Solo Veterinarios y Administradores pueden crear/editar; Tutores consultan las de sus mascotas.
    """
    queryset = FichaClinica.objects.select_related('mascota', 'mascota__tutor', 'profesional', 'cita').all()
    serializer_class = FichaClinicaSerializer
    permission_classes = [IsVeterinarioOrAdmin]
    filterset_fields = ['mascota', 'profesional', 'cita']
    search_fields = ['mascota__nombre', 'diagnostico', 'tratamiento', 'receta_medica', 'examenes_solicitados']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.rol == 'TUTOR' and not user.is_superuser:
            return qs.filter(mascota__tutor__usuario=user)
        return qs


class ControlVacunaViewSet(viewsets.ModelViewSet):
    """
    CRUD del Módulo de Recordatorios de Vacunación, Desparasitación y Controles Periódicos.
    """
    queryset = ControlVacuna.objects.select_related('mascota', 'mascota__tutor', 'profesional').all()
    serializer_class = ControlVacunaSerializer
    permission_classes = [IsVeterinarioOrAdmin]
    filterset_fields = ['mascota', 'tipo', 'estado']
    search_fields = ['nombre_vacuna_control', 'mascota__nombre', 'mascota__tutor__nombres', 'lote_serie']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.rol == 'TUTOR' and not user.is_superuser:
            return qs.filter(mascota__tutor__usuario=user)
        return qs

    @action(detail=False, methods=['get'])
    def alertas(self, request):
        """Retorna los recordatorios pendientes vencidos o próximos a vencer en los siguientes 30 días."""
        limite = timezone.localdate() + timedelta(days=30)
        pendientes = self.get_queryset().filter(
            estado=ControlVacuna.Estados.PENDIENTE,
            fecha_proximo_control__lte=limite
        ).order_by('fecha_proximo_control')
        return Response(ControlVacunaSerializer(pendientes, many=True).data)

    @action(detail=True, methods=['post'])
    def marcar_aplicado(self, request, pk=None):
        """Registra la aplicación efectiva de la vacuna/control en la fecha actual."""
        control = self.get_object()
        control.estado = ControlVacuna.Estados.APLICADO
        control.fecha_aplicacion = timezone.localdate()
        control.save()
        return Response(ControlVacunaSerializer(control).data)


class DashboardResumenView(APIView):
    """Entrega métricas ejecutivas y equipo médico activo en tiempo real para la portada y tablero de PetCare."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        hoy = timezone.localdate()
        limite_alerta = hoy + timedelta(days=15)
        medicos_activos = Profesional.objects.select_related('usuario').filter(
            activo=True
        ).filter(
            Q(usuario__isnull=True) | Q(usuario__is_active=True)
        )
        equipo = [
            {
                'id': p.id,
                'nombre_completo': p.nombre_completo,
                'especialidad': p.get_especialidad_display(),
                'horario': f"{p.hora_inicio_jornada.strftime('%H:%M')} a {p.hora_fin_jornada.strftime('%H:%M')} hrs",
                'bloque_min': p.duracion_bloque_min,
            }
            for p in medicos_activos
        ]
        return Response({
            'total_tutores': Tutor.objects.count(),
            'total_mascotas': Mascota.objects.filter(activo=True).count(),
            'total_profesionales': len(equipo),
            'citas_hoy': CitaMedica.objects.filter(
                fecha=hoy,
                estado__in=[CitaMedica.Estados.PROGRAMADA, CitaMedica.Estados.CONFIRMADA]
            ).count(),
            'total_fichas': FichaClinica.objects.count(),
            'alertas_vacunas': ControlVacuna.objects.filter(
                estado=ControlVacuna.Estados.PENDIENTE,
                fecha_proximo_control__lte=limite_alerta
            ).count(),
            'equipo_medico': equipo,
            'fecha_servidor': hoy.isoformat(),
        })
