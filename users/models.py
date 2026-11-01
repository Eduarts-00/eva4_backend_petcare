"""
Modelo de Usuario Personalizado con Control de Acceso Basado en Roles (RBAC).
Alumno: Angel Eduardo Lara Manriquez
Docente: Marcelo Alvarado Aravena
Año: 2026
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Extiende el usuario nativo de Django incorporando rangos específicos
    del dominio veterinario PetCare (Administrador, Médico Veterinario y Tutor).
    """

    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador / Recepción'
        VETERINARIO = 'VETERINARIO', 'Médico Veterinario'
        TUTOR = 'TUTOR', 'Tutor de Mascota'

    rol = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.TUTOR,
        verbose_name='Rol en Clínica'
    )
    rut = models.CharField(max_length=15, blank=True, verbose_name='RUT')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    debe_cambiar_password = models.BooleanField(
        default=False,
        verbose_name='Cambio de Contraseña Obligatorio'
    )

    class Meta:
        verbose_name = 'Usuario del Sistema'
        verbose_name_plural = 'Usuarios del Sistema'
        ordering = ['username']

    def save(self, *args, **kwargs):
        # Sincronizar privilegios de administración según el rango del usuario
        if self.rol == self.Roles.ADMIN or self.is_superuser:
            self.rol = self.Roles.ADMIN
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False
        super().save(*args, **kwargs)

    def __str__(self):
        nombre = self.get_full_name() or self.username
        return f"{nombre} ({self.get_rol_display()})"
