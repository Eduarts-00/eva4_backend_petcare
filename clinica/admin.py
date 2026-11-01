"""
Configuración avanzada y personalizada del Administrador de Django para PetCare (Criterio 2).
Incluye Inlines relacionales, filtros laterales, buscadores, acciones masivas y badges HTML.
"""
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Profesional, Tutor, Mascota, CitaMedica, FichaClinica, ControlVacuna


class MascotaInline(admin.TabularInline):
    model = Mascota
    extra = 0
    fields = ('nombre', 'especie', 'raza', 'sexo', 'peso_kg', 'esterilizado', 'activo')
    show_change_link = True


class FichaClinicaInline(admin.StackedInline):
    model = FichaClinica
    extra = 0
    fields = ('profesional', 'fecha_atencion', 'peso_actual_kg', 'temperatura_c', 'diagnostico', 'tratamiento', 'receta_medica')
    show_change_link = True


class ControlVacunaInline(admin.TabularInline):
    model = ControlVacuna
    extra = 0
    fields = ('tipo', 'nombre_vacuna_control', 'fecha_aplicacion', 'fecha_proximo_control', 'estado')
    show_change_link = True


@admin.register(Profesional)
class ProfesionalAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut', 'especialidad_badge', 'horario_texto', 'duracion_bloque_min', 'telefono', 'activo')
    list_filter = ('especialidad', 'activo')
    search_fields = ('nombre_completo', 'rut', 'email')
    list_editable = ('activo',)

    @admin.display(description='Especialidad')
    def especialidad_badge(self, obj):
        return format_html(
            '<span style="background:#0f766e;color:#fff;padding:3px 9px;border-radius:10px;font-size:11px;font-weight:600;">{}</span>',
            obj.get_especialidad_display(),
        )

    @admin.display(description='Jornada de Atención')
    def horario_texto(self, obj):
        return f"{obj.hora_inicio_jornada.strftime('%H:%M')} - {obj.hora_fin_jornada.strftime('%H:%M')}"


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo_col', 'rut', 'telefono', 'email', 'direccion', 'cantidad_mascotas')
    search_fields = ('rut', 'nombres', 'apellidos', 'email', 'telefono')
    list_filter = ('fecha_registro',)
    inlines = [MascotaInline]

    @admin.display(description='Tutor Responsable')
    def nombre_completo_col(self, obj):
        return obj.nombre_completo

    @admin.display(description='Mascotas Registradas')
    def cantidad_mascotas(self, obj):
        total = obj.mascotas.count()
        return format_html('<strong>🐾 {}</strong>', total)


@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especie_icono', 'raza', 'sexo', 'tutor', 'peso_kg', 'esterilizado', 'activo')
    list_filter = ('especie', 'sexo', 'esterilizado', 'activo')
    search_fields = ('nombre', 'raza', 'microchip', 'tutor__nombres', 'tutor__apellidos', 'tutor__rut')
    autocomplete_fields = ('tutor',)
    inlines = [FichaClinicaInline, ControlVacunaInline]

    @admin.display(description='Especie')
    def especie_icono(self, obj):
        iconos = {
            'PERRO': '🐶 Perro',
            'GATO': '🐱 Gato',
            'AVE': '🦜 Ave',
            'EXOTICO': '🐹 Exótico',
            'OTRO': '🐾 Otro',
        }
        return iconos.get(obj.especie, obj.get_especie_display())


@admin.register(CitaMedica)
class CitaMedicaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'bloque_horario', 'mascota', 'tutor_nombre', 'profesional', 'motivo', 'estado_badge')
    list_filter = ('estado', 'fecha', 'profesional')
    search_fields = ('mascota__nombre', 'mascota__tutor__nombres', 'mascota__tutor__rut', 'profesional__nombre_completo', 'motivo')
    date_hierarchy = 'fecha'
    autocomplete_fields = ('mascota', 'profesional')
    actions = ['marcar_confirmadas', 'marcar_atendidas', 'marcar_canceladas']

    @admin.display(description='Horario')
    def bloque_horario(self, obj):
        fin = obj.hora_fin.strftime('%H:%M') if obj.hora_fin else ''
        return f"{obj.hora_inicio.strftime('%H:%M')} - {fin}"

    @admin.display(description='Tutor')
    def tutor_nombre(self, obj):
        return obj.mascota.tutor.nombre_completo

    @admin.display(description='Estado')
    def estado_badge(self, obj):
        colores = {
            'PROGRAMADA': '#0284c7',
            'CONFIRMADA': '#0d9488',
            'ATENDIDA': '#16a34a',
            'CANCELADA': '#dc2626',
        }
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;">{}</span>',
            colores.get(obj.estado, '#64748b'),
            obj.get_estado_display(),
        )

    @admin.action(description='Confirmar citas seleccionadas')
    def marcar_confirmadas(self, request, queryset):
        queryset.update(estado=CitaMedica.Estados.CONFIRMADA)

    @admin.action(description='Marcar citas seleccionadas como Atendidas')
    def marcar_atendidas(self, request, queryset):
        queryset.update(estado=CitaMedica.Estados.ATENDIDA)

    @admin.action(description='Cancelar citas seleccionadas')
    def marcar_canceladas(self, request, queryset):
        queryset.update(estado=CitaMedica.Estados.CANCELADA)


@admin.register(FichaClinica)
class FichaClinicaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_atencion', 'mascota', 'profesional', 'peso_actual_kg', 'temperatura_c', 'resumen_diagnostico')
    list_filter = ('profesional', 'fecha_atencion', 'mascota__especie')
    search_fields = ('mascota__nombre', 'mascota__tutor__rut', 'diagnostico', 'tratamiento', 'receta_medica', 'examenes_solicitados')
    date_hierarchy = 'fecha_atencion'
    autocomplete_fields = ('mascota', 'profesional', 'cita')

    @admin.display(description='Diagnóstico')
    def resumen_diagnostico(self, obj):
        return (obj.diagnostico[:55] + '...') if len(obj.diagnostico) > 55 else obj.diagnostico


@admin.register(ControlVacuna)
class ControlVacunaAdmin(admin.ModelAdmin):
    list_display = ('nombre_vacuna_control', 'tipo', 'mascota', 'tutor_contacto', 'fecha_aplicacion', 'fecha_proximo_control', 'semaforo_alerta')
    list_filter = ('tipo', 'estado', 'fecha_proximo_control')
    search_fields = ('nombre_vacuna_control', 'lote_serie', 'mascota__nombre', 'mascota__tutor__nombres', 'mascota__tutor__rut')
    date_hierarchy = 'fecha_proximo_control'
    autocomplete_fields = ('mascota', 'profesional')
    actions = ['marcar_como_aplicado']

    @admin.display(description='Tutor / Teléfono')
    def tutor_contacto(self, obj):
        return f"{obj.mascota.tutor.nombre_completo} ({obj.mascota.tutor.telefono})"

    @admin.display(description='Semáforo Seguimiento')
    def semaforo_alerta(self, obj):
        alerta = obj.nivel_alerta
        config = {
            'VENCIDO': ('#dc2626', f'🔴 Vencido ({abs(obj.dias_restantes)}d)'),
            'PROXIMO': ('#d97706', f'🟡 Próximo (en {obj.dias_restantes}d)'),
            'AL_DIA': ('#0284c7', f'🟢 Programado ({obj.dias_restantes}d)'),
            'COMPLETADO': ('#16a34a', '✅ Aplicado'),
            'CANCELADO': ('#6b7280', '⚪ Cancelado'),
        }
        color, texto = config.get(alerta, ('#6b7280', alerta))
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;">{}</span>',
            color,
            texto,
        )

    @admin.action(description='Registrar aplicación hoy (Marcar como Aplicado)')
    def marcar_como_aplicado(self, request, queryset):
        queryset.update(estado=ControlVacuna.Estados.APLICADO, fecha_aplicacion=timezone.localdate())
