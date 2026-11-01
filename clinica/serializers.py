"""
Serializadores DRF para los modelos clínicos de PetCare.
Convierte validaciones de dominio (como bloqueo de solapamiento de citas) en respuestas JSON claras.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from users.models import CustomUser
from .models import Profesional, Tutor, Mascota, CitaMedica, FichaClinica, ControlVacuna


class ProfesionalSerializer(serializers.ModelSerializer):
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    username_cuenta = serializers.SerializerMethodField()
    cuenta_activa = serializers.SerializerMethodField()
    debe_cambiar_password = serializers.SerializerMethodField()

    # Campos de escritura para que el Administrador cree y reparta la cuenta al contratar un médico
    nuevo_username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password_temporal = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Profesional
        fields = [
            'id', 'usuario', 'username_cuenta', 'cuenta_activa', 'debe_cambiar_password',
            'nuevo_username', 'password_temporal',
            'rut', 'nombre_completo', 'especialidad',
            'especialidad_display', 'email', 'telefono',
            'hora_inicio_jornada', 'hora_fin_jornada', 'duracion_bloque_min', 'activo'
        ]

    def get_username_cuenta(self, obj):
        return obj.usuario.username if obj.usuario_id and obj.usuario else None

    def get_cuenta_activa(self, obj):
        if obj.usuario_id and obj.usuario:
            return obj.usuario.is_active and obj.activo
        return obj.activo

    def get_debe_cambiar_password(self, obj):
        return bool(obj.usuario.debe_cambiar_password) if (obj.usuario_id and obj.usuario) else False

    def validate(self, attrs):
        nuevo_username = (attrs.get('nuevo_username') or '').strip()
        password_temporal = attrs.get('password_temporal') or ''
        if nuevo_username:
            if CustomUser.objects.filter(username=nuevo_username).exists():
                raise serializers.ValidationError({
                    'nuevo_username': f"El nombre de usuario '{nuevo_username}' ya está en uso."
                })
            if len(password_temporal) < 6:
                raise serializers.ValidationError({
                    'password_temporal': 'La clave temporal inicial debe tener al menos 6 caracteres.'
                })
        return attrs

    def create(self, validated_data):
        nuevo_username = (validated_data.pop('nuevo_username', '') or '').strip()
        password_temporal = validated_data.pop('password_temporal', '') or ''

        with transaction.atomic():
            if nuevo_username and not validated_data.get('usuario'):
                partes = (validated_data.get('nombre_completo') or '').strip().split(' ', 1)
                first_name = partes[0] if partes else nuevo_username
                last_name = partes[1] if len(partes) > 1 else ''

                vet_user = CustomUser(
                    username=nuevo_username,
                    email=validated_data.get('email', ''),
                    first_name=first_name,
                    last_name=last_name,
                    rol=CustomUser.Roles.VETERINARIO,
                    rut=validated_data.get('rut', ''),
                    telefono=validated_data.get('telefono', ''),
                    is_active=True,
                    debe_cambiar_password=True,
                )
                vet_user.set_password(password_temporal)
                vet_user.save()
                validated_data['usuario'] = vet_user

            return super().create(validated_data)


class MascotaResumenSerializer(serializers.ModelSerializer):
    especie_display = serializers.CharField(source='get_especie_display', read_only=True)

    class Meta:
        model = Mascota
        fields = ['id', 'nombre', 'especie', 'especie_display', 'raza', 'peso_kg']


class TutorSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    mascotas = MascotaResumenSerializer(many=True, read_only=True)
    total_mascotas = serializers.IntegerField(source='mascotas.count', read_only=True)

    class Meta:
        model = Tutor
        fields = [
            'id', 'usuario', 'rut', 'nombres', 'apellidos', 'nombre_completo',
            'telefono', 'email', 'direccion', 'fecha_registro', 'total_mascotas', 'mascotas'
        ]


class MascotaSerializer(serializers.ModelSerializer):
    tutor_nombre = serializers.CharField(source='tutor.nombre_completo', read_only=True)
    tutor_rut = serializers.CharField(source='tutor.rut', read_only=True)
    tutor_telefono = serializers.CharField(source='tutor.telefono', read_only=True)
    especie_display = serializers.CharField(source='get_especie_display', read_only=True)
    sexo_display = serializers.CharField(source='get_sexo_display', read_only=True)

    class Meta:
        model = Mascota
        fields = [
            'id', 'tutor', 'tutor_nombre', 'tutor_rut', 'tutor_telefono',
            'nombre', 'especie', 'especie_display', 'raza', 'sexo', 'sexo_display',
            'fecha_nacimiento', 'peso_kg', 'color', 'microchip',
            'esterilizado', 'alergias_notas', 'activo', 'creado_en'
        ]


class CitaMedicaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    mascota_especie = serializers.CharField(source='mascota.get_especie_display', read_only=True)
    tutor_nombre = serializers.CharField(source='mascota.tutor.nombre_completo', read_only=True)
    profesional_nombre = serializers.CharField(source='profesional.nombre_completo', read_only=True)
    profesional_especialidad = serializers.CharField(source='profesional.get_especialidad_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tiene_ficha = serializers.SerializerMethodField()

    class Meta:
        model = CitaMedica
        fields = [
            'id', 'mascota', 'mascota_nombre', 'mascota_especie', 'tutor_nombre',
            'profesional', 'profesional_nombre', 'profesional_especialidad',
            'fecha', 'hora_inicio', 'hora_fin', 'motivo',
            'estado', 'estado_display', 'observaciones', 'tiene_ficha', 'creado_en'
        ]

    def get_tiene_ficha(self, obj):
        return hasattr(obj, 'ficha_clinica')

    def validate(self, attrs):
        instance = self.instance or CitaMedica()
        for field, value in attrs.items():
            setattr(instance, field, value)
        try:
            instance.clean()
            attrs['hora_fin'] = instance.hora_fin
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages)
        return attrs


class FichaClinicaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    tutor_nombre = serializers.CharField(source='mascota.tutor.nombre_completo', read_only=True)
    profesional_nombre = serializers.CharField(source='profesional.nombre_completo', read_only=True)

    class Meta:
        model = FichaClinica
        fields = [
            'id', 'mascota', 'mascota_nombre', 'tutor_nombre',
            'profesional', 'profesional_nombre', 'cita',
            'fecha_atencion', 'peso_actual_kg', 'temperatura_c',
            'anamnesis', 'diagnostico', 'tratamiento',
            'receta_medica', 'examenes_solicitados', 'observaciones'
        ]


class ControlVacunaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    mascota_especie = serializers.CharField(source='mascota.get_especie_display', read_only=True)
    tutor_nombre = serializers.CharField(source='mascota.tutor.nombre_completo', read_only=True)
    tutor_telefono = serializers.CharField(source='mascota.tutor.telefono', read_only=True)
    profesional_nombre = serializers.CharField(source='profesional.nombre_completo', read_only=True, default='')
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    dias_restantes = serializers.IntegerField(read_only=True)
    nivel_alerta = serializers.CharField(read_only=True)

    class Meta:
        model = ControlVacuna
        fields = [
            'id', 'mascota', 'mascota_nombre', 'mascota_especie',
            'tutor_nombre', 'tutor_telefono', 'profesional', 'profesional_nombre',
            'tipo', 'tipo_display', 'nombre_vacuna_control', 'lote_serie',
            'fecha_aplicacion', 'fecha_proximo_control', 'estado', 'estado_display',
            'dias_restantes', 'nivel_alerta', 'notas', 'creado_en'
        ]
