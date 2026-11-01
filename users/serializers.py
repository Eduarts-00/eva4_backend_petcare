"""
Serializadores para autenticación, sesiones, registro de tutores y cambio seguro de contraseña.
"""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personaliza el payload del JWT para incluir rol, nombre completo, estado y cambio obligatorio de clave.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['rol'] = user.rol
        token['nombre_completo'] = user.get_full_name() or user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'nombre_completo': self.user.get_full_name() or self.user.username,
            'rol': self.user.rol,
            'rol_display': self.user.get_rol_display(),
            'is_staff': self.user.is_staff or self.user.is_superuser,
            'is_active': self.user.is_active,
            'debe_cambiar_password': self.user.debe_cambiar_password,
        }
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializador de lectura para el perfil del usuario en sesión."""
    nombre_completo = serializers.SerializerMethodField()
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'nombre_completo', 'rol', 'rol_display', 'rut', 'telefono',
            'is_staff', 'is_active', 'debe_cambiar_password'
        ]

    def get_nombre_completo(self, obj):
        return obj.get_full_name() or obj.username


class CambiarPasswordSeguraSerializer(serializers.Serializer):
    """
    Valida el cambio obligatorio o voluntario de contraseña exigiendo estándares de seguridad clínica.
    """
    password_actual = serializers.CharField(write_only=True, required=True)
    password_nueva = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirmacion = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate(self, attrs):
        user = self.context['request'].user
        actual = attrs['password_actual']
        nueva = attrs['password_nueva']
        confirmacion = attrs['password_confirmacion']

        if not user.check_password(actual):
            raise serializers.ValidationError({'password_actual': 'La contraseña temporal o actual no es correcta.'})

        if nueva != confirmacion:
            raise serializers.ValidationError({'password_confirmacion': 'La confirmación no coincide con la nueva contraseña.'})

        if nueva == actual:
            raise serializers.ValidationError({'password_nueva': 'La nueva contraseña debe ser diferente a la clave temporal entregada.'})

        errores_fortaleza = []
        if len(nueva) < 8:
            errores_fortaleza.append('Debe tener al menos 8 caracteres.')
        if not any(c.isupper() for c in nueva):
            errores_fortaleza.append('Debe incluir al menos una letra mayúscula.')
        if not any(c.islower() for c in nueva):
            errores_fortaleza.append('Debe incluir al menos una letra minúscula.')
        if not any(c.isdigit() for c in nueva):
            errores_fortaleza.append('Debe incluir al menos un número.')

        if errores_fortaleza:
            raise serializers.ValidationError({'password_nueva': ' '.join(errores_fortaleza)})

        try:
            validate_password(nueva, user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password_nueva': ' '.join(exc.messages)})

        return attrs


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    """
    Permite registrar un nuevo usuario Tutor vinculándolo automáticamente
    con una ficha de Tutor en la base de datos clínica.
    """
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password',
            'first_name', 'last_name', 'rut', 'telefono'
        ]

    def create(self, validated_data):
        from clinica.models import Tutor

        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.rol = CustomUser.Roles.TUTOR
        user.debe_cambiar_password = False
        user.set_password(password)
        user.save()

        # Crear perfil de Tutor asociado si proporcionó RUT o datos básicos
        rut_limpio = (user.rut or f"USR-{user.id}").strip()
        if not Tutor.objects.filter(rut=rut_limpio).exists():
            Tutor.objects.create(
                usuario=user,
                rut=rut_limpio,
                nombres=user.first_name or user.username,
                apellidos=user.last_name or 'Registrado Web',
                telefono=user.telefono or '+56900000000',
                email=user.email or f"{user.username}@petcare.cl",
                direccion='Por confirmar en recepción',
            )
        return user
