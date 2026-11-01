"""
Personalización del Administrador de Django para el modelo CustomUser (Criterio 2).
Incluye control de cuentas activas/bloqueadas y estado de clave temporal.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'nombre_completo', 'email', 'badge_rol',
        'rut', 'estado_seguridad', 'debe_cambiar_password', 'is_active'
    )
    list_filter = ('rol', 'is_active', 'debe_cambiar_password', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'rut')
    actions = ['bloquear_cuentas', 'rehabilitar_cuentas']

    fieldsets = UserAdmin.fieldsets + (
        ('Información Clínica y Seguridad PetCare', {
            'fields': ('rol', 'rut', 'telefono', 'debe_cambiar_password'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Clínica y Seguridad PetCare', {
            'fields': ('first_name', 'last_name', 'email', 'rol', 'rut', 'telefono', 'debe_cambiar_password'),
        }),
    )

    @admin.display(description='Nombre Completo')
    def nombre_completo(self, obj):
        return obj.get_full_name() or '—'

    @admin.display(description='Rol Asignado')
    def badge_rol(self, obj):
        colores = {
            'ADMIN': '#0d6efd',
            'VETERINARIO': '#198754',
            'TUTOR': '#6c757d',
        }
        color = colores.get(obj.rol, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-weight:600;font-size:11px;">{}</span>',
            color,
            obj.get_rol_display(),
        )

    @admin.display(description='Estado Cuenta')
    def estado_seguridad(self, obj):
        if not obj.is_active:
            return format_html(
                '<span style="background:#dc2626;color:#fff;padding:3px 9px;border-radius:10px;font-size:11px;font-weight:700;">🔒 Bloqueada</span>'
            )
        if obj.debe_cambiar_password:
            return format_html(
                '<span style="background:#d97706;color:#fff;padding:3px 9px;border-radius:10px;font-size:11px;font-weight:700;">🔑 Clave Temporal</span>'
            )
        return format_html(
            '<span style="background:#16a34a;color:#fff;padding:3px 9px;border-radius:10px;font-size:11px;font-weight:700;">🟢 Habilitada</span>'
        )

    @admin.action(description='🔒 Bloquear / Inhabilitar cuentas seleccionadas')
    def bloquear_cuentas(self, request, queryset):
        queryset.exclude(pk=request.user.pk).update(is_active=False)

    @admin.action(description='🔓 Rehabilitar cuentas seleccionadas')
    def rehabilitar_cuentas(self, request, queryset):
        queryset.update(is_active=True)
