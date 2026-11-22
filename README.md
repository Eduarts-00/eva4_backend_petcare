# 🐾 PetCare — Sistema Distribuido de Gestión Veterinaria (Evaluación N.º 4)

**Asignatura:** Programación Backend — Unidad 3: Aplicación API RESTful – Arquitectura AWS, Integración y Seguridad  
**Evaluación:** Evaluación N.º 4 (Ponderación 30% / 100 puntos: 80 pts Práctica + 20 pts Defensa Oral)  
**Docente:** Marcelo Alvarado Aravena  
**Estudiante:** Angel Eduardo Lara Manriquez — Sección `IEC-N4-C2` (2026)  
**Repositorio Evaluación 4:** `https://github.com/Eduarts-00/eva4_backend_petcare.git`  
**Repositorio Base (Evaluación 3):** `https://github.com/Eduarts-00/eva3_petcare.git`  

---

## 🌐 Enlaces de Producción y Arquitectura AWS

- **Portal Web Frontend / Backend Integrado (HTTPS):** `https://petcaree.duckdns.org/`
- **Centro Interactivo AWS & Seguridad (EVA 4):** Botón **`🛡️ AWS & Seguridad (EVA 4)`** en la barra superior del portal.
- **Panel Django Admin (Sesión Unificada RBAC):** `https://petcaree.duckdns.org/admin/`
- **Documentación Interactiva OpenAPI / Swagger:** `https://petcaree.duckdns.org/api/docs/`
- **Telemetría de Arquitectura AWS en Vivo (JSON):** `https://petcaree.duckdns.org/api/aws/estado/`
- **Verificación Criptográfica PBKDF2 y Salt (JSON):** `https://petcaree.duckdns.org/api/auth/verificar-hash/`
- **Generador de URLs Prefirmadas S3 SigV4 (JSON):** `https://petcaree.duckdns.org/api/aws/s3-presigned-url/`
- **Endpoint de Prueba de Rate Limiting / Throttling:** `https://petcaree.duckdns.org/api/aws/rate-limit-test/`

---

## 🏗️ Arquitectura Obligatoria Implementada (Sección 3)

| Componente | Implementación en PetCare EVA 4 | Evidencia / Ubicación en Código |
| :--- | :--- | :--- |
| **EC2 Frontend** | Interfaz Web SPA responsiva (`templates/index.html`) que consume la API vía JSON + JWT `Bearer` y soporta enrutamiento directo hacia Amazon API Gateway | `templates/index.html` |
| **EC2 Backend** | Aplicación Django 5 + Django REST Framework servida con Gunicorn y Nginx | `petcare_config/`, `clinica/`, `users/` |
| **RDS PostgreSQL** | Persistencia relacional separada (7 entidades), Security Group restringido a TCP `5432` desde EC2 Backend, cifrado KMS en reposo y TLS (`sslmode=require`) | `petcare_config/settings.py`, `/api/aws/estado/` |
| **Amazon S3** | Bucket con `Block Public Access = ON`, cifrado en reposo `SSE-S3 (AES256)` y acceso controlado mediante **URLs Prefirmadas (`AWS4-HMAC-SHA256`)** | `clinica/views.py` (`S3PresignedUrlView`) |
| **API Gateway** | Exposición de endpoints REST y control de *Rate Limiting / Throttling* (`Rate: 2 req/s, Burst: 5`), verificado con respuestas `200 OK` seguidas de `429 Too Many Requests` | `scripts/probar_rate_limit.py`, `/api/aws/rate-limit-test/` |
| **CloudWatch + SNS** | Monitoreo de métricas (`CPUUtilization`, `NetworkIn/Out`, `StatusCheckFailed`) y alarma conectada a tópico de notificación por correo en **Amazon SNS** | `petcare_config/settings.py` (`LOGGING`), `INFORME_TECNICO_EVA4.md` |
| **SonarQube (SAST)** | Análisis estático de código Python/Django y remediación de secretos en duro (`python:S2068`) mediante variables de entorno (`_get_env_secret`) | `sonar-project.properties`, `INFORME_TECNICO_EVA4.md` |
| **OWASP ZAP (DAST)** | Análisis dinámico sobre la aplicación desplegada y endurecimiento de cabeceras HTTP (`CSP`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `HttpOnly`) | `petcare_config/middleware.py` (`SecurityHeadersAndCORSMiddleware`) |
| **JWT + Criptografía** | Autenticación `Bearer` con `SimpleJWT` (`HS256`), autorización RBAC (`ADMIN`, `VETERINARIO`, `TUTOR`) y almacenamiento de contraseñas con `PBKDF2-HMAC-SHA256` + `Salt` aleatorio de 128 bits | `users/views.py` (`VerificarCriptografiaPasswordView`), `scripts/verificar_criptografia.py` |
| **Respaldos RDS + Lambda 7h** | Respaldos automáticos de RDS, Snapshot manual y automatización exacta **cada 7 horas** mediante **Amazon EventBridge Scheduler (`rate(7 hours)`) + AWS Lambda + AWS SNS** | `aws_infra/lambda_rds_backup_7h.py` |

---

## ⚡ Actualización Rápida en la Máquina Virtual AWS EC2

Para actualizar la instancia EC2 existente de `eva3_petcare` con todos los componentes de la **Evaluación N.º 4**, ejecuta en la terminal de la máquina virtual Ubuntu:

```bash
curl -sSL https://raw.githubusercontent.com/Eduarts-00/eva4_backend_petcare/main/deploy_aws.sh | sudo bash
```

---

## 🧪 Scripts de Verificación para la Defensa Práctica

### 1. Demostrar Rate Limiting / Throttling (`200 OK` -> `429 Too Many Requests`)
```bash
# Contra el endpoint de la aplicación o la Invoke URL de Amazon API Gateway:
python scripts/probar_rate_limit.py https://petcaree.duckdns.org/api/aws/rate-limit-test/
```

### 2. Demostrar Hashing PBKDF2-HMAC-SHA256 y Unicidad del Salt Criptográfico
```bash
python scripts/verificar_criptografia.py
```

### 3. Ejecutar Suite Completa de Pruebas Automatizadas (EVA 3 + EVA 4)
```bash
python manage.py test
```

---

## 🔑 Credenciales de Prueba (Pobladas con `poblar_datos.py`)

| Rol en el Sistema | Usuario | Contraseña | Permisos y Comportamiento |
| :--- | :--- | :--- | :--- |
| **Administrador / Recepción** | `admin` | `petcare2026` | Control total Web, contratación/bloqueo de médicos y acceso unificado a `/admin/` |
| **Médico Veterinario (Activo)** | `dra_camila` | `petcare2026` | Estación Médica: Citas sin solapamiento, Fichas Clínicas y Vacunas |
| **Médico Recién Contratado** | `dra_valentina` | `Temporal2026!` | Clave temporal: al ingresar abre ventana obligatoria de cambio de contraseña segura |
| **Tutor de Mascota** | `tutor_carlos` | `petcare2026` | Inscripción de sus mascotas, consulta de recetas/vacunas y reserva de citas |

---

## 📚 Documentación y Entregables de la Evaluación N.º 4

- **[`INFORME_TECNICO_EVA4.md`](./INFORME_TECNICO_EVA4.md):** Informe técnico integral con arquitectura AWS, SAST (SonarQube) vs DAST (OWASP ZAP), criptografía de contraseñas, API Gateway Rate Limiting, seguridad en RDS y S3, monitoreo en CloudWatch, respaldos cada 7 horas con EventBridge + Lambda y **Banco Completo de Respuestas para la Defensa Oral (Bloques A, B, C y D)**.
- **[`prompts_ia.md`](./prompts_ia.md):** Evidencia de uso de IA con recomendaciones de seguridad contrastadas con documentación oficial (OWASP, Django Docs, AWS Well-Architected Framework) y justificación de aplicación/descarte.
