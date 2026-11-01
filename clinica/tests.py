"""
Pruebas automatizadas del dominio PetCare (EVA 3).
Valida:
1. Bloqueo de solapamiento de citas médicas para un mismo veterinario.
2. Actualización automática de peso y estado ATENDIDA al emitir Ficha Clínica.
3. Cálculo del semáforo de alertas en Recordatorios de Vacunación.
4. Seguridad y autenticación por rol en la API REST.
"""
from datetime import time, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from users.models import CustomUser
from .models import Profesional, Tutor, Mascota, CitaMedica, FichaClinica, ControlVacuna


class PetCareDomainTests(TestCase):

    def setUp(self):
        self.hoy = timezone.localdate()
        self.vet_user = CustomUser.objects.create_user(
            username='vet_test', password='password123', rol=CustomUser.Roles.VETERINARIO
        )
        self.profesional = Profesional.objects.create(
            usuario=self.vet_user,
            rut='15.111.222-3',
            nombre_completo='Dra. Prueba Clínica',
            especialidad=Profesional.Especialidades.GENERAL,
            email='vet@petcare.cl',
            telefono='+56911111111',
            hora_inicio_jornada=time(9, 0),
            hora_fin_jornada=time(18, 0),
        )
        self.tutor = Tutor.objects.create(
            rut='12.333.444-5',
            nombres='Juan',
            apellidos='Pérez',
            telefono='+56922222222',
            email='juan@correo.cl',
            direccion='Santiago',
        )
        self.mascota1 = Mascota.objects.create(
            tutor=self.tutor, nombre='Max', especie=Mascota.Especies.PERRO, peso_kg=10.0
        )
        self.mascota2 = Mascota.objects.create(
            tutor=self.tutor, nombre='Mia', especie=Mascota.Especies.GATO, peso_kg=4.0
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.vet_user)

    def test_bloqueo_solapamiento_citas(self):
        """Verifica que la API rechace una segunda cita en el mismo horario y profesional."""
        r1 = self.client.post('/api/citas/', {
            'mascota': self.mascota1.id,
            'profesional': self.profesional.id,
            'fecha': self.hoy.isoformat(),
            'hora_inicio': '10:00',
            'motivo': 'Control sano',
        }, format='json')
        self.assertEqual(r1.status_code, 201)

        # Intentar agendar otra mascota a las 10:15 con el mismo profesional (solapada con 10:00-10:30)
        r2 = self.client.post('/api/citas/', {
            'mascota': self.mascota2.id,
            'profesional': self.profesional.id,
            'fecha': self.hoy.isoformat(),
            'hora_inicio': '10:15',
            'motivo': 'Vacunación',
        }, format='json')
        self.assertEqual(r2.status_code, 400)
        self.assertIn('hora_inicio', r2.data)

    def test_ficha_clinica_actualiza_peso_y_cita(self):
        """Al crear una Ficha Clínica desde una cita, marca la cita ATENDIDA y actualiza el peso."""
        cita = CitaMedica.objects.create(
            mascota=self.mascota1,
            profesional=self.profesional,
            fecha=self.hoy,
            hora_inicio=time(11, 0),
            motivo='Consulta general',
        )
        ficha = FichaClinica.objects.create(
            mascota=self.mascota1,
            profesional=self.profesional,
            cita=cita,
            peso_actual_kg=11.5,
            temperatura_c=38.6,
            anamnesis='Buen apetito',
            diagnostico='Paciente sano',
            tratamiento='Control en 6 meses',
        )
        cita.refresh_from_db()
        self.mascota1.refresh_from_db()
        self.assertEqual(cita.estado, CitaMedica.Estados.ATENDIDA)
        self.assertEqual(float(self.mascota1.peso_kg), 11.5)
        self.assertIsNotNone(ficha.id)

    def test_semaforo_recordatorios_vacunas(self):
        """Verifica que el nivel de alerta detecte vacunas vencidas y próximas."""
        vencida = ControlVacuna.objects.create(
            mascota=self.mascota1,
            nombre_vacuna_control='Antirrábica',
            fecha_proximo_control=self.hoy - timedelta(days=3),
        )
        proxima = ControlVacuna.objects.create(
            mascota=self.mascota2,
            nombre_vacuna_control='Triple Felina',
            fecha_proximo_control=self.hoy + timedelta(days=5),
        )
        self.assertEqual(vencida.nivel_alerta, 'VENCIDO')
        self.assertEqual(proxima.nivel_alerta, 'PROXIMO')

    def test_ruta_desconocida_redirige_al_inicio(self):
        """Verifica que cualquier URL inexistente (ej. /dfsffsd) redirija automáticamente a '/'."""
        resp = self.client.get('/dfsffsd')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/')

    def test_contratacion_medico_cambio_password_y_bloqueo_cuenta(self):
        """
        Verifica el flujo completo de recursos humanos y seguridad clínica:
        1) ADMIN contrata un médico creando su cuenta con clave temporal (debe_cambiar_password=True).
        2) El nuevo médico inicia sesión y cambia su clave por una segura (debe_cambiar_password=False).
        3) ADMIN bloquea/inhabilita la cuenta por protección o despido y el login queda denegado (403).
        """
        admin_user = CustomUser.objects.create_user(
            username='admin_rrhh', password='password123', rol=CustomUser.Roles.ADMIN
        )
        admin_client = APIClient()
        admin_client.force_authenticate(user=admin_user)

        # 1. Contratar nuevo médico con credenciales temporales
        r_alta = admin_client.post('/api/profesionales/', {
            'nombre_completo': 'Pedro Lagos Vera',
            'rut': '16.999.888-7',
            'especialidad': 'CIRUGIA',
            'email': 'pedro.lagos@petcare.cl',
            'telefono': '+56944445555',
            'hora_inicio_jornada': '09:00',
            'hora_fin_jornada': '17:00',
            'duracion_bloque_min': 30,
            'nuevo_username': 'dr_pedro',
            'password_temporal': 'Temporal2026!',
        }, format='json')
        self.assertEqual(r_alta.status_code, 201)
        prof_id = r_alta.data['id']
        self.assertTrue(r_alta.data['debe_cambiar_password'])

        # 2. Nuevo médico ingresa con su clave temporal y la cambia por una segura
        recluta_client = APIClient()
        r_login = recluta_client.post('/api/auth/login/', {
            'username': 'dr_pedro',
            'password': 'Temporal2026!',
        }, format='json')
        self.assertEqual(r_login.status_code, 200)
        self.assertTrue(r_login.data['user']['debe_cambiar_password'])

        recluta_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r_login.data['access']}")
        r_cambio = recluta_client.post('/api/auth/cambiar-password/', {
            'password_actual': 'Temporal2026!',
            'password_nueva': 'SeguraVet2026!',
            'password_confirmacion': 'SeguraVet2026!',
        }, format='json')
        self.assertEqual(r_cambio.status_code, 200)
        self.assertFalse(r_cambio.data['user']['debe_cambiar_password'])

        # 3. Administrador bloquea/inhabilita al médico
        r_bloq = admin_client.post(
            f'/api/profesionales/{prof_id}/cambiar_estado_cuenta/',
            {'activo': False},
            format='json',
        )
        self.assertEqual(r_bloq.status_code, 200)
        self.assertFalse(r_bloq.data['profesional']['cuenta_activa'])

        # Intentar volver a iniciar sesión con la cuenta bloqueada -> 403 Forbidden
        anon_client = APIClient()
        r_denegado = anon_client.post('/api/auth/login/', {
            'username': 'dr_pedro',
            'password': 'SeguraVet2026!',
        }, format='json')
        self.assertEqual(r_denegado.status_code, 403)
        self.assertTrue(r_denegado.data.get('cuenta_bloqueada'))
