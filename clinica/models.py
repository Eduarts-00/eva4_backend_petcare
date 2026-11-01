"""
Modelos relacionales del dominio veterinario PetCare (PostgreSQL + Django ORM).
Cubre los 4 módulos del caso de evaluación:
1. Tutores y Mascotas.
2. Calendario/Agendamiento de Citas con disponibilidad por profesional y bloqueo de solapamiento.
3. Ficha Clínica Digital (diagnósticos, tratamientos, recetas y exámenes).
4. Recordatorios de Vacunación y Controles Periódicos.

Alumno: Angel Eduardo Lara Manriquez
Docente: Marcelo Alvarado Aravena
Año: 2026
"""
from datetime import time, timedelta, datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Profesional(models.Model):
    """Médico Veterinario con horario de disponibilidad configurable."""

    class Especialidades(models.TextChoices):
        GENERAL = 'MEDICINA_GENERAL', 'Medicina General'
        CIRUGIA = 'CIRUGIA', 'Cirugía y Traumatología'
        DERMATOLOGIA = 'DERMATOLOGIA', 'Dermatología Veterinaria'
        EXOTICOS = 'EXOTICOS', 'Animales Exóticos'
        FELINA = 'MEDICINA_FELINA', 'Medicina Felina'

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfil_profesional',
        verbose_name='Cuenta de Usuario'
    )
    rut = models.CharField(max_length=15, unique=True, verbose_name='RUT Profesional')
    nombre_completo = models.CharField(max_length=120, verbose_name='Nombre Completo')
    especialidad = models.CharField(
        max_length=30,
        choices=Especialidades.choices,
        default=Especialidades.GENERAL,
        verbose_name='Especialidad'
    )
    email = models.EmailField(verbose_name='Correo Electrónico')
    telefono = models.CharField(max_length=20, verbose_name='Teléfono')
    hora_inicio_jornada = models.TimeField(default=time(9, 0), verbose_name='Inicio Jornada')
    hora_fin_jornada = models.TimeField(default=time(18, 0), verbose_name='Fin Jornada')
    duracion_bloque_min = models.PositiveIntegerField(default=30, verbose_name='Duración Bloque (min)')
    activo = models.BooleanField(default=True, verbose_name='Activo en Agenda')

    class Meta:
        verbose_name = 'Médico Veterinario'
        verbose_name_plural = 'Médicos Veterinarios'
        ordering = ['nombre_completo']

    def __str__(self):
        return f"Dr(a). {self.nombre_completo} — {self.get_especialidad_display()}"


class Tutor(models.Model):
    """Propietario o responsable legal de una o más mascotas."""
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfil_tutor',
        verbose_name='Cuenta de Usuario'
    )
    rut = models.CharField(max_length=15, unique=True, verbose_name='RUT Tutor')
    nombres = models.CharField(max_length=80, verbose_name='Nombres')
    apellidos = models.CharField(max_length=80, verbose_name='Apellidos')
    telefono = models.CharField(max_length=20, verbose_name='Teléfono de Contacto')
    email = models.EmailField(verbose_name='Correo Electrónico')
    direccion = models.CharField(max_length=200, verbose_name='Dirección')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')

    class Meta:
        verbose_name = 'Tutor'
        verbose_name_plural = 'Tutores'
        ordering = ['apellidos', 'nombres']

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"


class Mascota(models.Model):
    """Paciente veterinario vinculado a un Tutor."""

    class Especies(models.TextChoices):
        PERRO = 'PERRO', 'Perro'
        GATO = 'GATO', 'Gato'
        AVE = 'AVE', 'Ave'
        EXOTICO = 'EXOTICO', 'Exótico / Pequeño Mamífero'
        OTRO = 'OTRO', 'Otro'

    class Sexos(models.TextChoices):
        MACHO = 'MACHO', 'Macho'
        HEMBRA = 'HEMBRA', 'Hembra'

    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE,
        related_name='mascotas',
        verbose_name='Tutor Responsable'
    )
    nombre = models.CharField(max_length=80, verbose_name='Nombre de la Mascota')
    especie = models.CharField(
        max_length=20,
        choices=Especies.choices,
        default=Especies.PERRO,
        verbose_name='Especie'
    )
    raza = models.CharField(max_length=80, default='Mestizo', verbose_name='Raza')
    sexo = models.CharField(
        max_length=10,
        choices=Sexos.choices,
        default=Sexos.MACHO,
        verbose_name='Sexo'
    )
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de Nacimiento')
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, verbose_name='Peso (kg)')
    color = models.CharField(max_length=50, blank=True, verbose_name='Color / Pelaje')
    microchip = models.CharField(max_length=40, blank=True, verbose_name='N° Microchip')
    esterilizado = models.BooleanField(default=False, verbose_name='Esterilizado(a)')
    alergias_notas = models.TextField(blank=True, verbose_name='Alergias / Antecedentes')
    activo = models.BooleanField(default=True, verbose_name='Paciente Activo')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mascota'
        verbose_name_plural = 'Mascotas'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_especie_display()} - Tutor: {self.tutor.nombre_completo})"


class CitaMedica(models.Model):
    """
    Agendamiento médico con validación estricta anti-solapamiento de horarios
    tanto por Profesional como por Mascota.
    """

    class Estados(models.TextChoices):
        PROGRAMADA = 'PROGRAMADA', 'Programada'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        ATENDIDA = 'ATENDIDA', 'Atendida'
        CANCELADA = 'CANCELADA', 'Cancelada'

    mascota = models.ForeignKey(
        Mascota,
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name='Mascota Paciente'
    )
    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.PROTECT,
        related_name='citas',
        verbose_name='Médico Veterinario'
    )
    fecha = models.DateField(verbose_name='Fecha de la Cita', db_index=True)
    hora_inicio = models.TimeField(verbose_name='Hora Inicio')
    hora_fin = models.TimeField(verbose_name='Hora Término', blank=True, null=True)
    motivo = models.CharField(max_length=200, verbose_name='Motivo de Consulta')
    estado = models.CharField(
        max_length=15,
        choices=Estados.choices,
        default=Estados.PROGRAMADA,
        verbose_name='Estado de la Cita'
    )
    observaciones = models.TextField(blank=True, verbose_name='Observaciones de Recepción')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cita Médica'
        verbose_name_plural = 'Citas Médicas'
        ordering = ['fecha', 'hora_inicio']

    def calcular_hora_fin_por_defecto(self):
        """Si no se indica hora_fin, asigna automáticamente el bloque del profesional (ej. 30 min)."""
        if self.hora_inicio and not self.hora_fin:
            duracion = self.profesional.duracion_bloque_min if self.profesional_id else 30
            dt_inicio = datetime.combine(datetime.today(), self.hora_inicio)
            self.hora_fin = (dt_inicio + timedelta(minutes=duracion)).time()

    def clean(self):
        """Valida reglas de negocio: horario laboral y ausencia total de solapamiento."""
        self.calcular_hora_fin_por_defecto()

        if self.hora_inicio and self.hora_fin and self.hora_fin <= self.hora_inicio:
            raise ValidationError({'hora_fin': 'La hora de término debe ser posterior a la hora de inicio.'})

        if self.profesional_id and self.hora_inicio and self.hora_fin:
            if not self.profesional.activo:
                raise ValidationError({'profesional': 'El profesional seleccionado no se encuentra activo en agenda.'})
            if (
                self.hora_inicio < self.profesional.hora_inicio_jornada
                or self.hora_fin > self.profesional.hora_fin_jornada
            ):
                raise ValidationError({
                    'hora_inicio': (
                        f"El horario debe estar dentro de la jornada del Dr(a). {self.profesional.nombre_completo}: "
                        f"{self.profesional.hora_inicio_jornada.strftime('%H:%M')} a "
                        f"{self.profesional.hora_fin_jornada.strftime('%H:%M')}."
                    )
                })

        # Solo validar cruces si la cita no está cancelada
        if self.estado != self.Estados.CANCELADA and self.fecha and self.hora_inicio and self.hora_fin:
            estados_activos = [self.Estados.PROGRAMADA, self.Estados.CONFIRMADA, self.Estados.ATENDIDA]

            if self.profesional_id:
                solapadas_prof = CitaMedica.objects.filter(
                    profesional_id=self.profesional_id,
                    fecha=self.fecha,
                    estado__in=estados_activos,
                    hora_inicio__lt=self.hora_fin,
                    hora_fin__gt=self.hora_inicio,
                ).exclude(pk=self.pk)
                if solapadas_prof.exists():
                    conflicto = solapadas_prof.first()
                    raise ValidationError({
                        'hora_inicio': (
                            f"Conflicto de horario (Solapamiento bloqueado): El Dr(a). {self.profesional.nombre_completo} "
                            f"ya tiene una cita agendada de {conflicto.hora_inicio.strftime('%H:%M')} a "
                            f"{conflicto.hora_fin.strftime('%H:%M')} con el paciente '{conflicto.mascota.nombre}'."
                        )
                    })

            if self.mascota_id:
                solapadas_masc = CitaMedica.objects.filter(
                    mascota_id=self.mascota_id,
                    fecha=self.fecha,
                    estado__in=estados_activos,
                    hora_inicio__lt=self.hora_fin,
                    hora_fin__gt=self.hora_inicio,
                ).exclude(pk=self.pk)
                if solapadas_masc.exists():
                    raise ValidationError({
                        'mascota': 'Esta mascota ya tiene otra atención agendada en ese mismo bloque horario.'
                    })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fecha} {self.hora_inicio.strftime('%H:%M')} — {self.mascota.nombre} con Dr(a). {self.profesional.nombre_completo}"


class FichaClinica(models.Model):
    """
    Ficha Clínica Digital inmutable de cada atención médica:
    almacena diagnósticos, tratamientos, recetas médicas y exámenes solicitados.
    """
    mascota = models.ForeignKey(
        Mascota,
        on_delete=models.CASCADE,
        related_name='fichas_clinicas',
        verbose_name='Mascota Paciente'
    )
    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.PROTECT,
        related_name='fichas_emitidas',
        verbose_name='Médico Tratante'
    )
    cita = models.OneToOneField(
        CitaMedica,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ficha_clinica',
        verbose_name='Cita Asociada'
    )
    fecha_atencion = models.DateTimeField(default=timezone.now, verbose_name='Fecha y Hora de Atención')
    peso_actual_kg = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Peso Registrado (kg)')
    temperatura_c = models.DecimalField(max_digits=4, decimal_places=1, default=38.5, verbose_name='Temperatura (°C)')
    anamnesis = models.TextField(verbose_name='Anamnesis / Síntomas Reportados')
    diagnostico = models.TextField(verbose_name='Diagnóstico Clínico')
    tratamiento = models.TextField(verbose_name='Tratamiento Indicado')
    receta_medica = models.TextField(blank=True, verbose_name='Receta Médica (Fármacos y Posología)')
    examenes_solicitados = models.TextField(blank=True, verbose_name='Exámenes Complementarios')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones Adicionales')

    class Meta:
        verbose_name = 'Ficha Clínica Digital'
        verbose_name_plural = 'Fichas Clínicas Digitales'
        ordering = ['-fecha_atencion']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar peso actual de la mascota automáticamente
        if self.peso_actual_kg and self.mascota_id:
            Mascota.objects.filter(pk=self.mascota_id).update(peso_kg=self.peso_actual_kg)
        # Si proviene de una cita, marcarla automáticamente como ATENDIDA
        if self.cita_id:
            CitaMedica.objects.filter(pk=self.cita_id).update(estado=CitaMedica.Estados.ATENDIDA)

    def __str__(self):
        return f"Ficha #{self.id} — {self.mascota.nombre} ({self.fecha_atencion.strftime('%d/%m/%Y')})"


class ControlVacuna(models.Model):
    """
    Módulo de seguimiento y recordatorios para Vacunación, Desparasitación
    y Controles Periódicos con sistema de alertas por vencimiento.
    """

    class Tipos(models.TextChoices):
        VACUNA = 'VACUNA', 'Vacunación'
        DESPARASITACION = 'DESPARASITACION', 'Desparasitación Interna/Externa'
        CONTROL_PERIODICO = 'CONTROL_PERIODICO', 'Control Sano / Periódico'

    class Estados(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente (Recordatorio Activo)'
        APLICADO = 'APLICADO', 'Aplicado / Realizado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    mascota = models.ForeignKey(
        Mascota,
        on_delete=models.CASCADE,
        related_name='recordatorios_vacunas',
        verbose_name='Mascota Paciente'
    )
    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacunas_registradas',
        verbose_name='Profesional Responsable'
    )
    tipo = models.CharField(
        max_length=25,
        choices=Tipos.choices,
        default=Tipos.VACUNA,
        verbose_name='Tipo de Control'
    )
    nombre_vacuna_control = models.CharField(
        max_length=120,
        verbose_name='Vacuna / Control (ej. Óctuple, Antirrábica)'
    )
    lote_serie = models.CharField(max_length=60, blank=True, verbose_name='N° Lote / Serie')
    fecha_aplicacion = models.DateField(null=True, blank=True, verbose_name='Última Fecha de Aplicación')
    fecha_proximo_control = models.DateField(verbose_name='Fecha Próxima Dosis / Control', db_index=True)
    estado = models.CharField(
        max_length=15,
        choices=Estados.choices,
        default=Estados.PENDIENTE,
        verbose_name='Estado de Seguimiento'
    )
    notas = models.TextField(blank=True, verbose_name='Indicaciones para el Tutor')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recordatorio de Vacuna / Control'
        verbose_name_plural = 'Recordatorios de Vacunación y Controles'
        ordering = ['fecha_proximo_control']

    @property
    def dias_restantes(self):
        hoy = timezone.localdate()
        return (self.fecha_proximo_control - hoy).days

    @property
    def nivel_alerta(self):
        """Calcula el semáforo clínico del recordatorio."""
        if self.estado == self.Estados.APLICADO:
            return 'COMPLETADO'
        if self.estado == self.Estados.CANCELADO:
            return 'CANCELADO'
        dias = self.dias_restantes
        if dias < 0:
            return 'VENCIDO'
        if dias <= 15:
            return 'PROXIMO'
        return 'AL_DIA'

    def __str__(self):
        return f"{self.nombre_vacuna_control} — {self.mascota.nombre} (Próx: {self.fecha_proximo_control})"
