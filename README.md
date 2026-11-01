# 🐾 PetCare — Sistema de Gestión de Citas y Fichas Médicas para Veterinaria

**Asignatura:** Desarrollo Backend — Evaluación Parcial N°3  
**Docente:** Marcelo Alvarado Aravena  
**Estudiante:** Angel Eduardo Lara Manriquez — Sección `IEC-N4-C2` (2026)  

---

## 🌐 Despliegue en AWS EC2 (Producción)

- **URL Aplicación Web Pública:** `http://98.85.49.169/`
- **Panel Django Admin (Sesión Unificada):** `http://98.85.49.169/admin/`
- **Documentación Swagger / OpenAPI:** `http://98.85.49.169/api/docs/`

---

## 📌 Descripción del Proyecto

**PetCare** resuelve los problemas críticos de solapamiento de citas médicas, extravío de fichas clínicas en papel y falta de seguimiento de vacunas mediante una aplicación web Fullstack construida sobre **Django 5 + Django REST Framework (DRF) + PostgreSQL**, desplegada en **AWS EC2** con **Gunicorn** y **Nginx**.

### Funcionalidades Principales (4 Módulos del Caso)
1. **CRUD de Tutores y Mascotas:** Registro relacional de propietarios y pacientes con búsqueda instantánea por RUT, nombre, raza o microchip.
2. **Calendario y Agendamiento sin Solapamiento:** Consulta dinámica de bloques horarios disponibles por Médico Veterinario y validación atómica que impide cruces de horario tanto para el profesional como para la mascota.
3. **Ficha Clínica Digital:** Registro estructurado de anamnesis, diagnóstico, tratamiento, receta médica, exámenes solicitados, temperatura y actualización automática del peso del paciente.
4. **Recordatorios de Vacunación y Controles Periódicos:** Seguimiento con semáforo automático de alertas (`🔴 Vencido`, `🟡 Próximo ≤15 días`, `🟢 Al día`, `✅ Aplicado`).

---

## 🔑 Credenciales de Prueba (Pobladas con `poblar_datos.py`)

| Rol en el Sistema | Usuario | Contraseña | Permisos y Comportamiento |
| :--- | :--- | :--- | :--- |
| **Administrador / Recepción** | `admin` | `petcare2026` | Control total Web, contratación/bloqueo de médicos y acceso unificado a `/admin/` |
| **Médico Veterinario (Activo)** | `dra_camila` | `petcare2026` | Estación Médica: Citas sin solapamiento, Fichas Clínicas y Vacunas |
| **Médico Recién Contratado** | `dra_valentina` | `Temporal2026!` | Clave temporal: al ingresar abre ventana obligatoria de cambio de contraseña segura |
| **Tutor de Mascota** | `tutor_carlos` | `petcare2026` | Inscripción de sus mascotas, consulta de recetas/vacunas y reserva de citas |

---

## 🛠️ Instrucciones de Ejecución Local

### 1. Requisitos Previos
- Python 3.11+
- PostgreSQL 14+ ejecutándose en `localhost:5432`

### 2. Instalación y Configuración
```bash
# 1. Crear y activar entorno virtual
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno (opcional, valores por defecto en settings.py)
# DB_NAME=petcare_db | DB_USER=postgres | DB_PASSWORD=inacap.2030 | DB_HOST=localhost | DB_PORT=5432

# 4. Aplicar migraciones en PostgreSQL
python manage.py makemigrations
python manage.py migrate

# 5. Cargar datos iniciales de demostración
python poblar_datos.py

# 6. Iniciar servidor de desarrollo
python manage.py runserver
```

Luego abrir en el navegador:
- **Portal Web PetCare:** `http://127.0.0.1:8000/`
- **Django Admin:** `http://127.0.0.1:8000/admin/`
- **Swagger API:** `http://127.0.0.1:8000/api/docs/`

---

## 📡 Principales Endpoints REST

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login/` | Inicia sesión (crea sesión Django + retorna JWT con rol) |
| `GET` | `/api/dashboard/resumen/` | KPIs en tiempo real (pacientes, citas hoy, fichas, alertas) |
| `GET/POST/PUT/DELETE` | `/api/tutores/` | CRUD completo de Tutores |
| `GET/POST/PUT/DELETE` | `/api/mascotas/` | CRUD completo de Mascotas |
| `GET` | `/api/profesionales/{id}/disponibilidad/?fecha=YYYY-MM-DD` | Bloques horarios libres/ocupados del veterinario |
| `GET/POST/PUT/DELETE` | `/api/citas/` | Agendamiento con validación anti-solapamiento |
| `GET/POST/PUT/DELETE` | `/api/fichas-clinicas/` | Gestión de Fichas Clínicas Digitales |
| `GET/POST/PUT/DELETE` | `/api/recordatorios/` | Gestión de Vacunas y Controles Periódicos |
| `GET` | `/api/recordatorios/alertas/` | Alertas vencidas o próximas (≤30 días) |

---

## 🤖 Evidencia de Uso de IA
Revisar el archivo [`prompts_ia.md`](./prompts_ia.md) incluido en la raíz de este repositorio.
