"""
Script idempotente de carga de datos iniciales para demostración y defensa de PetCare (EVA 3).
Ejecutar con: python poblar_datos.py
"""
import os
from datetime import time, timedelta
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petcare_config.settings')
django.setup()

from django.utils import timezone
from users.models import CustomUser
from clinica.models import Profesional, Tutor, Mascota, CitaMedica, FichaClinica, ControlVacuna


def run():
    hoy = timezone.localdate()

    # 1. Usuarios con roles diferenciados
    admin_user, _ = CustomUser.objects.update_or_create(
        username='admin',
        defaults={
            'first_name': 'Angel',
            'last_name': 'Lara (Recepción)',
            'email': 'admin@petcare.cl',
            'rol': CustomUser.Roles.ADMIN,
            'rut': '20.111.222-3',
            'telefono': '+56988881111',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    admin_user.set_password('petcare2026')
    admin_user.save()

    vet_camila_user, _ = CustomUser.objects.update_or_create(
        username='dra_camila',
        defaults={
            'first_name': 'Camila',
            'last_name': 'Soto',
            'email': 'camila.soto@petcare.cl',
            'rol': CustomUser.Roles.VETERINARIO,
            'rut': '17.456.789-0',
            'telefono': '+56977772222',
            'is_staff': False,
            'is_active': True,
            'debe_cambiar_password': False,
        }
    )
    vet_camila_user.set_password('petcare2026')
    vet_camila_user.save()

    vet_matias_user, _ = CustomUser.objects.update_or_create(
        username='dr_matias',
        defaults={
            'first_name': 'Matías',
            'last_name': 'Rojas',
            'email': 'matias.rojas@petcare.cl',
            'rol': CustomUser.Roles.VETERINARIO,
            'rut': '16.890.123-K',
            'telefono': '+56966663333',
            'is_staff': False,
            'is_active': True,
            'debe_cambiar_password': False,
        }
    )
    vet_matias_user.set_password('petcare2026')
    vet_matias_user.save()

    vet_valentina_user, _ = CustomUser.objects.update_or_create(
        username='dra_valentina',
        defaults={
            'first_name': 'Valentina',
            'last_name': 'Muñoz',
            'email': 'valentina.munoz@petcare.cl',
            'rol': CustomUser.Roles.VETERINARIO,
            'rut': '18.901.234-5',
            'telefono': '+56955554444',
            'is_staff': False,
            'is_active': True,
            'debe_cambiar_password': True,
        }
    )
    vet_valentina_user.set_password('Temporal2026!')
    vet_valentina_user.save()

    tutor_carlos_user, _ = CustomUser.objects.update_or_create(
        username='tutor_carlos',
        defaults={
            'first_name': 'Carlos',
            'last_name': 'Mendoza',
            'email': 'carlos.mendoza@correo.cl',
            'rol': CustomUser.Roles.TUTOR,
            'rut': '15.222.333-4',
            'telefono': '+56991234567',
        }
    )
    tutor_carlos_user.set_password('petcare2026')
    tutor_carlos_user.save()

    # 2. Profesionales Veterinarios
    prof_camila, _ = Profesional.objects.update_or_create(
        rut='17.456.789-0',
        defaults={
            'usuario': vet_camila_user,
            'nombre_completo': 'Camila Soto Valdés',
            'especialidad': Profesional.Especialidades.GENERAL,
            'email': 'camila.soto@petcare.cl',
            'telefono': '+56977772222',
            'hora_inicio_jornada': time(9, 0),
            'hora_fin_jornada': time(18, 0),
            'duracion_bloque_min': 30,
            'activo': True,
        }
    )

    prof_matias, _ = Profesional.objects.update_or_create(
        rut='16.890.123-K',
        defaults={
            'usuario': vet_matias_user,
            'nombre_completo': 'Matías Rojas Herrera',
            'especialidad': Profesional.Especialidades.CIRUGIA,
            'email': 'matias.rojas@petcare.cl',
            'telefono': '+56966663333',
            'hora_inicio_jornada': time(10, 0),
            'hora_fin_jornada': time(17, 0),
            'duracion_bloque_min': 30,
            'activo': True,
        }
    )

    prof_valentina, _ = Profesional.objects.update_or_create(
        rut='18.901.234-5',
        defaults={
            'usuario': vet_valentina_user,
            'nombre_completo': 'Valentina Muñoz Díaz',
            'especialidad': Profesional.Especialidades.FELINA,
            'email': 'valentina.munoz@petcare.cl',
            'telefono': '+56955554444',
            'hora_inicio_jornada': time(9, 30),
            'hora_fin_jornada': time(17, 30),
            'duracion_bloque_min': 30,
            'activo': True,
        }
    )

    # 3. Tutores
    tutor_carlos, _ = Tutor.objects.update_or_create(
        rut='15.222.333-4',
        defaults={
            'usuario': tutor_carlos_user,
            'nombres': 'Carlos Andrés',
            'apellidos': 'Mendoza Pérez',
            'telefono': '+56991234567',
            'email': 'carlos.mendoza@correo.cl',
            'direccion': 'Av. Providencia 1450, Santiago',
        }
    )

    tutor_daniela, _ = Tutor.objects.update_or_create(
        rut='18.765.432-1',
        defaults={
            'nombres': 'Daniela Paz',
            'apellidos': 'Fuentes Lagos',
            'telefono': '+56982345678',
            'email': 'daniela.fuentes@correo.cl',
            'direccion': 'Los Leones 820, Ñuñoa',
        }
    )

    tutor_rodrigo, _ = Tutor.objects.update_or_create(
        rut='14.333.888-2',
        defaults={
            'nombres': 'Rodrigo Ignacio',
            'apellidos': 'Silva Contreras',
            'telefono': '+56973456789',
            'email': 'rodrigo.silva@correo.cl',
            'direccion': 'Av. Macul 3210, Macul',
        }
    )

    # 4. Mascotas
    thor, _ = Mascota.objects.update_or_create(
        tutor=tutor_carlos,
        nombre='Thor',
        defaults={
            'especie': Mascota.Especies.PERRO,
            'raza': 'Golden Retriever',
            'sexo': Mascota.Sexos.MACHO,
            'fecha_nacimiento': hoy - timedelta(days=365 * 3),
            'peso_kg': 29.5,
            'color': 'Dorado',
            'microchip': '981098102938471',
            'esterilizado': True,
            'alergias_notas': 'Sensibilidad alimentaria leve al pollo.',
        }
    )

    luna, _ = Mascota.objects.update_or_create(
        tutor=tutor_carlos,
        nombre='Luna',
        defaults={
            'especie': Mascota.Especies.GATO,
            'raza': 'Doméstico Pelo Corto',
            'sexo': Mascota.Sexos.HEMBRA,
            'fecha_nacimiento': hoy - timedelta(days=365 * 2),
            'peso_kg': 4.1,
            'color': 'Blanco y Gris',
            'microchip': '981098102938499',
            'esterilizado': True,
        }
    )

    michi, _ = Mascota.objects.update_or_create(
        tutor=tutor_daniela,
        nombre='Simba',
        defaults={
            'especie': Mascota.Especies.GATO,
            'raza': 'Naranjo Europeo',
            'sexo': Mascota.Sexos.MACHO,
            'fecha_nacimiento': hoy - timedelta(days=500),
            'peso_kg': 4.8,
            'color': 'Naranjo atigrado',
            'esterilizado': True,
        }
    )

    rocky, _ = Mascota.objects.update_or_create(
        tutor=tutor_rodrigo,
        nombre='Rocky',
        defaults={
            'especie': Mascota.Especies.PERRO,
            'raza': 'Bulldog Francés',
            'sexo': Mascota.Sexos.MACHO,
            'fecha_nacimiento': hoy - timedelta(days=800),
            'peso_kg': 12.4,
            'color': 'Leonado',
            'esterilizado': False,
            'alergias_notas': 'Dermatitis atópica estacional.',
        }
    )

    # 5. Citas Médicas sin solapamiento
    if not CitaMedica.objects.exists():
        cita_atendida = CitaMedica.objects.create(
            mascota=thor,
            profesional=prof_camila,
            fecha=hoy,
            hora_inicio=time(9, 30),
            motivo='Otitis externa oído derecho y revisión general',
            estado=CitaMedica.Estados.ATENDIDA,
        )
        CitaMedica.objects.create(
            mascota=michi,
            profesional=prof_camila,
            fecha=hoy,
            hora_inicio=time(11, 0),
            motivo='Control preventivo anual felino',
            estado=CitaMedica.Estados.CONFIRMADA,
        )
        CitaMedica.objects.create(
            mascota=rocky,
            profesional=prof_matias,
            fecha=hoy,
            hora_inicio=time(12, 0),
            motivo='Evaluación prequirúrgica esterilización',
            estado=CitaMedica.Estados.PROGRAMADA,
        )
        CitaMedica.objects.create(
            mascota=luna,
            profesional=prof_valentina,
            fecha=hoy + timedelta(days=1),
            hora_inicio=time(10, 30),
            motivo='Refuerzo vacuna Triple Felina',
            estado=CitaMedica.Estados.CONFIRMADA,
        )

        # 6. Fichas Clínicas Digitales
        FichaClinica.objects.create(
            mascota=thor,
            profesional=prof_camila,
            cita=cita_atendida,
            peso_actual_kg=29.5,
            temperatura_c=38.7,
            anamnesis='Tutor reporta sacudidas frecuentes de cabeza y prurito auricular desde hace 3 días.',
            diagnostico='Otitis externa eritemato-ceruminosa bilateral leve.',
            tratamiento='Limpieza ótica clínica con solución fisiológica tibia y terapia tópica por 7 días.',
            receta_medica='1. Otiflex Limpiador: aplicar 5 gotas previo a medicación.\n2. Posatex Suspensión Ótica: 4 gotas cada 24 hrs por 7 días.',
            examenes_solicitados='Citología de secreción ótica (control en 10 días).',
        )

        FichaClinica.objects.create(
            mascota=rocky,
            profesional=prof_matias,
            peso_actual_kg=12.4,
            temperatura_c=38.4,
            anamnesis='Prurito interdigital y enrojecimiento abdominal.',
            diagnostico='Brote leve de dermatitis alérgica ambiental.',
            tratamiento='Baño medicado con clorhexidina al 2% semanal y control antiparasitario externo.',
            receta_medica='Apoquel 5.4 mg: medio comprimido cada 12 hrs por 5 días, luego cada 24 hrs por 7 días.',
            examenes_solicitados='Raspado cutáneo descartando Demodex (negativo).',
        )

    # 7. Recordatorios de Vacunación y Controles Periódicos
    if not ControlVacuna.objects.exists():
        ControlVacuna.objects.create(
            mascota=thor,
            profesional=prof_camila,
            tipo=ControlVacuna.Tipos.VACUNA,
            nombre_vacuna_control='Vacuna Antirrábica Anual',
            lote_serie='RAB-2025-88',
            fecha_aplicacion=hoy - timedelta(days=370),
            fecha_proximo_control=hoy - timedelta(days=5),
            estado=ControlVacuna.Estados.PENDIENTE,
            notas='Dosis anual vencida hace 5 días. Contactar al tutor.',
        )
        ControlVacuna.objects.create(
            mascota=luna,
            profesional=prof_valentina,
            tipo=ControlVacuna.Tipos.VACUNA,
            nombre_vacuna_control='Vacuna Triple Felina',
            lote_serie='FEL-2025-41',
            fecha_aplicacion=hoy - timedelta(days=358),
            fecha_proximo_control=hoy + timedelta(days=7),
            estado=ControlVacuna.Estados.PENDIENTE,
            notas='Recordatorio próximo: vence en 7 días.',
        )
        ControlVacuna.objects.create(
            mascota=rocky,
            profesional=prof_matias,
            tipo=ControlVacuna.Tipos.DESPARASITACION,
            nombre_vacuna_control='Desparasitación Interna + Externa (Bravecto)',
            fecha_aplicacion=hoy - timedelta(days=80),
            fecha_proximo_control=hoy + timedelta(days=10),
            estado=ControlVacuna.Estados.PENDIENTE,
            notas='Próxima dosis trimestral.',
        )
        ControlVacuna.objects.create(
            mascota=michi,
            profesional=prof_valentina,
            tipo=ControlVacuna.Tipos.CONTROL_PERIODICO,
            nombre_vacuna_control='Vacuna Leucemia Felina (FeLV)',
            lote_serie='FELV-2026-12',
            fecha_aplicacion=hoy - timedelta(days=15),
            fecha_proximo_control=hoy + timedelta(days=350),
            estado=ControlVacuna.Estados.APLICADO,
            notas='Esquema al día.',
        )

    print('[OK] Datos iniciales de PetCare creados/verificados correctamente.')


if __name__ == '__main__':
    run()
