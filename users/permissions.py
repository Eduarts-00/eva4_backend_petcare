"""
Clases de permisos personalizadas en DRF para control de acceso por rango (ADMIN, VETERINARIO, TUTOR).
"""
from rest_framework import permissions


class IsAdminOrReadOnlyAuthenticated(permissions.BasePermission):
    """
    Solo el rango ADMIN puede crear, editar o eliminar Profesionales y Tutores.
    Veterinarios y Tutores autenticados pueden consultar según su alcance.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser or request.user.rol == 'ADMIN'


class IsStaffClinicoOrReadOnly(permissions.BasePermission):
    """
    Permite a ADMIN y VETERINARIO crear/editar mascotas, y a un TUTOR inscribir o actualizar
    únicamente sus propias mascotas (para poder agendar su primera hora), dejando DELETE exclusivo a ADMIN.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == 'DELETE':
            return request.user.is_superuser or request.user.rol == 'ADMIN'
        return request.user.is_superuser or request.user.rol in ('ADMIN', 'VETERINARIO', 'TUTOR')


class IsVeterinarioOrAdmin(permissions.BasePermission):
    """
    Permite emitir y actualizar Fichas Clínicas y Controles de Vacunación
    a Médicos Veterinarios y Administradores. Tutores consultan en solo lectura.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser or request.user.rol in ('ADMIN', 'VETERINARIO')
