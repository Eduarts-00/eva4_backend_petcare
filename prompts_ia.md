# Registro de Uso de Inteligencia Artificial y Validación de Seguridad (`prompts_ia.md`)

**Proyecto:** Sistema Distribuido de Gestión de Citas y Fichas Médicas para Veterinaria (**PetCare**)  
**Asignatura:** Programación Backend — Evaluación N.º 4 (Unidad 3: Arquitectura AWS, Integración y Seguridad)  
**Docente:** Marcelo Alvarado Aravena  
**Estudiante:** Angel Eduardo Lara Manriquez (Sección IEC-N4-C2)  
**Año:** 2026  

---

## 1. Propósito del Documento

En cumplimiento del **Resultado de Aprendizaje N.º 4**, la **Sección 5 (Entregable: Uso de IA)** y la **Sección 8 (Reglas para la aplicación)** de la Evaluación N.º 4:
> *"La IA podrá utilizarse para generar recomendaciones de seguridad, pero el estudiante deberá documentar al menos dos recomendaciones, contrastarlas con documentación oficial y justificar su aplicación o descarte."*

A continuación se documentan **cuatro recomendaciones de seguridad** generadas con apoyo de Inteligencia Artificial, su contraste riguroso con documentación técnica oficial (**Django Documentation**, **OWASP Cheat Sheet Series** y **AWS Well-Architected Security Pillar**) y la decisión técnica justificada de aplicación o descarte en **PetCare EVA 4**.

---

## 2. Recomendaciones de Seguridad Obtenidas de la IA, Contraste Oficial y Decisión Técnica

### Recomendación IA N.º 1 — Eliminación de secretos en duro (Hardcoded Secrets) y parametrización de TLS hacia Amazon RDS PostgreSQL
- **Prompt consultado a la IA:**  
  *"Analiza `petcare_config/settings.py` bajo criterios SAST (SonarQube) y seguridad de conexión hacia Amazon RDS PostgreSQL. ¿Qué vulnerabilidades detectas y cómo debo corregirlas?"*
- **Recomendación entregada por la IA:**  
  1. Sustituir cualquier literal de contraseña en `DATABASES['default']['PASSWORD']` y `SECRET_KEY` por lectura desde variables de entorno para eliminar el hallazgo `python:S2068` (*Hard-coded credentials are security-sensitive*) en SonarQube.  
  2. Forzar cifrado en tránsito (`OPTIONS: {'sslmode': 'require'}`) cuando `DB_HOST` apunte a una instancia de Amazon RDS (`*.rds.amazonaws.com`).
- **Contraste con Documentación Oficial:**  
  - **Documentación oficial de Django 5.1 (`Deployment checklist` — `SECRET_KEY` and `DATABASES`):** Establece que las credenciales de producción jamás deben almacenarse en el control de versiones Git y que las conexiones PostgreSQL remotas deben negociar TLS mediante el parámetro `sslmode` de `libpq`.  
  - **Documentación oficial de Amazon RDS (`Using SSL/TLS to encrypt a connection to a DB instance`):** Indica que RDS PostgreSQL genera certificados firmados por la CA de AWS y soporta `sslmode=require` o `verify-full` para cifrar el tráfico en el puerto TCP `5432`.
- **Decisión y Justificación Técnica (APLICADA):**  
  Se **aplicó íntegramente** en `petcare_config/settings.py` mediante la función `_get_env_secret()` y la detección automática `DB_IS_RDS`, configurando `'sslmode': 'require'` para conexiones hacia RDS y manteniendo compatibilidad con el entorno de pruebas local.

---

### Recomendación IA N.º 2 — Endurecimiento de Cabeceras HTTP (Mitigación de Alertas DAST de OWASP ZAP)
- **Prompt consultado a la IA:**  
  *"Al ejecutar un escaneo pasivo DAST con OWASP ZAP Baseline sobre una aplicación Django + Nginx, ¿qué alertas aparecen con mayor frecuencia y cómo se corrigen en el backend?"*
- **Recomendación entregada por la IA:**  
  Implementar un middleware en Django que inyecte explícitamente las cabeceras:
  - `Content-Security-Policy` (alerta ZAP `10038`)
  - `X-Content-Type-Options: nosniff` (alerta ZAP `10021`)
  - `X-Frame-Options: DENY` (alerta ZAP `10020` contra Clickjacking)
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()`
  - `Cache-Control: no-store, no-cache, must-revalidate, private` en rutas de autenticación (`/api/auth/`).
- **Contraste con Documentación Oficial:**  
  - **OWASP Secure Headers Project & OWASP REST Security Cheat Sheet:** Confirma que las APIs REST y aplicaciones híbridas deben declarar `X-Content-Type-Options: nosniff` para impedir ataques de *MIME-sniffing*, `frame-ancestors 'none'` / `X-Frame-Options: DENY` contra *Clickjacking*, y `Cache-Control: no-store` en endpoints que emiten tokens JWT (`/api/auth/login/`).
- **Decisión y Justificación Técnica (APLICADA):**  
  Se **aplicó** creando la clase `SecurityHeadersAndCORSMiddleware` en `petcare_config/middleware.py` y verificando su presencia mediante la prueba automatizada `test_eva4_owasp_zap_dast_security_headers` en `clinica/tests.py`.

---

### Recomendación IA N.º 3 — Distribución de Archivos en Amazon S3 mediante URLs Prefirmadas (`Presigned URLs`) vs. Hacer Público el Bucket S3
- **Prompt consultado a la IA:**  
  *"Necesito servir recetas médicas digitales y recursos desde un bucket Amazon S3 en Django. ¿Debo desactivar Block Public Access y aplicar una Bucket Policy pública `Principal: *`, o usar URLs prefirmadas?"*
- **Recomendación entregada por la IA:**  
  La IA presentó dos alternativas:  
  - *Alternativa A:* Desactivar *Block Public Access* y agregar una política `s3:GetObject` abierta a `"*"` para todo el bucket.  
  - *Alternativa B:* Mantener **Block Public Access = ON**, activar cifrado en reposo **SSE-S3 (`AES256`)** y generar **URLs Prefirmadas (`generate_presigned_url`)** con firma `AWS4-HMAC-SHA256` y expiración temporal (`900 segundos`) desde el backend Django.
- **Contraste con Documentación Oficial:**  
  - **AWS S3 Security Best Practices (`Blocking public access to your Amazon S3 storage`):** AWS recomienda enfáticamente mantener activado *Block Public Access* a nivel de bucket y cuenta, otorgando acceso temporal a objetos privados mediante *Presigned URLs* firmadas con credenciales IAM de privilegio mínimo.
- **Decisión y Justificación Técnica (ALTERNATIVA A DESCARTADA / ALTERNATIVA B APLICADA):**  
  Se **descartó** hacer público el bucket completo porque expone documentos clínicos de pacientes veterinarios (recetas, fichas) a enumeración o acceso no autorizado. Se **aplicó** la Alternativa B (`AWS_DEFAULT_ACL = None`, `AWS_QUERYSTRING_AUTH = True`, `AWS_QUERYSTRING_EXPIRE = 900` y vista `S3PresignedUrlView` en `/api/aws/s3-presigned-url/`).

---

### Recomendación IA N.º 4 — Automatización de Respaldos RDS Cada 7 Horas con EventBridge Scheduler + AWS Lambda
- **Prompt consultado a la IA:**  
  *"El caso de la Evaluación 4 pide explicar y diseñar cómo programar un respaldo de Amazon RDS PostgreSQL exactamente cada 7 horas. ¿Se puede hacer desde la configuración nativa de Automated Backups de RDS?"*
- **Recomendación entregada por la IA:**  
  Explicar que el sistema nativo de *Automated Backups* de Amazon RDS solo permite definir una **ventana diaria (cada 24 horas)** junto con *Point-in-Time Recovery (PITR)* mediante logs de transacciones cada 5 minutos, pero **no acepta un intervalo personalizado de 7 horas**. Para ejecutar snapshots exactamente cada 7 horas, se debe crear una regla en **Amazon EventBridge Scheduler** con la expresión `rate(7 hours)` que invoque una función **AWS Lambda** (`boto3.client('rds').create_db_snapshot(...)`) y envíe confirmación a un tópico de **Amazon SNS**.
- **Contraste con Documentación Oficial:**  
  - **Amazon RDS User Guide (`Working with backups`):** Confirma que los respaldos automáticos nativos se ejecutan una vez al día durante la *Backup Window* de 30 minutos.  
  - **Amazon EventBridge Scheduler Documentation (`Rate-based schedules`):** Documenta la sintaxis `rate(value unit)` donde `rate(7 hours)` dispara la ejecución periódica exacta cada 7 horas hacia destinos como AWS Lambda.
- **Decisión y Justificación Técnica (APLICADA):**  
  Se **aplicó** implementando la función serverless `aws_infra/lambda_rds_backup_7h.py` con rotación automática de snapshots antiguos y publicación de alertas en Amazon SNS, documentando la diferencia arquitectónica respecto del respaldo nativo de RDS.
