"""
Generador del Informe Técnico Oficial en formato Microsoft Word (.docx)
con Índice de Evidencias Numeradas y Capturas Reales de AWS incrustadas
para la Evaluación N.º 4 de Programación Backend (PetCare — Arquitectura AWS, Integración y Seguridad).
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def add_code_block(doc, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    r = p.add_run(text)
    r.font.name = 'Consolas'
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(15, 23, 42)


def add_evidence_image(doc, img_path: Path, title_text: str, description_text: str, width_inches: float = 6.0):
    h = doc.add_heading(title_text, level=2)
    for run in h.runs:
        run.font.color.rgb = RGBColor(15, 118, 110)
    p_desc = doc.add_paragraph(description_text)
    p_desc.italic = True
    if img_path.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_img = p_img.add_run()
        run_img.add_picture(str(img_path), width=Inches(width_inches))
    doc.add_paragraph()


def build_docx():
    base_dir = Path(__file__).resolve().parent.parent
    ev_dir = base_dir / 'evidencias_aws'

    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    # ==================== PORTADA ====================
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("INACAP — ÁREA TECNOLOGÍAS DE INFORMACIÓN Y CIBERSEGURIDAD\n")
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(15, 118, 110)

    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = h.add_run(
        "EVALUACIÓN N.º 4 — PROGRAMACIÓN BACKEND\n"
        "Unidad 3: Aplicación API RESTful – Arquitectura AWS, Integración y Seguridad\n"
        "Proyecto: PetCare — Sistema Distribuido de Gestión Clínica Veterinaria"
    )
    r2.bold = True
    r2.font.size = Pt(15)
    r2.font.color.rgb = RGBColor(30, 58, 138)

    meta = doc.add_paragraph()
    datos_portada = [
        ("Estudiante: ", "Angel Eduardo Lara Manriquez (Sección IEC-N4-C2)"),
        ("Docente: ", "Marcelo Alvarado Aravena"),
        ("Repositorio GitHub EVA 4: ", "https://github.com/Eduarts-00/eva4_backend_petcare.git"),
        ("Instancia 2 — EC2 Frontend Desacoplado: ", "http://3.230.130.63/ (eva4_petcare_FRONTEND)"),
        ("Instancia 1 — EC2 Backend DRF (HTTPS): ", "https://petcaree.duckdns.org/ (98.85.49.169 — i-0987fd370228da4bc)"),
        ("Amazon API Gateway (Rate Limit 2 req/s, Burst 5): ", "https://ozp0ipskkf.execute-api.us-east-1.amazonaws.com/prod"),
        ("Amazon RDS PostgreSQL 18.3 (TLS + KMS): ", "petcare-rds-postgres.cdsudpkituru.us-east-1.rds.amazonaws.com:5432"),
        ("Amazon S3 Bucket (SSE-S3 + Block Public Access): ", "petcare-eva4-static-media-2026-047602603714-us-east-1-an"),
        ("ARN Función AWS Lambda (Respaldo c/ 7 horas): ", "arn:aws:lambda:us-east-1:047602603714:function:PetCare-RDS-Backup-7h"),
    ]
    for lbl, val in datos_portada:
        run_lbl = meta.add_run(lbl)
        run_lbl.bold = True
        meta.add_run(val + "\n")

    # ==================== ÍNDICE DE EVIDENCIAS NUMERADAS ====================
    doc.add_heading("0. Índice Oficial de Evidencias Numeradas (Para Defensa de 5 Minutos)", level=1)
    doc.add_paragraph(
        "En cumplimiento del protocolo de defensa individual (Sección 7 de la pauta: 'las evidencias deberán "
        "estar entregadas, numeradas y accesibles antes de la clase'), la siguiente tabla indexa todas las "
        "evidencias prácticas y capturas reales de la infraestructura AWS implementada:"
    )

    evidencias_index = [
        ("N.º Evidencia", "Criterio / Actividad", "Componente AWS / Seguridad", "Descripción Verificable en este Informe"),
        ("Evidencia 01", "P3 / Sección 3", "Arquitectura Distribuida AWS", "Diagrama oficial con separación de EC2 Frontend, EC2 Backend DRF, RDS, S3, API Gateway y Lambda 7h."),
        ("Evidencia 02", "P3, P7 / Act. 5", "Amazon RDS PostgreSQL 18.3", "Captura de creación de instancia RDS (db.t4g.micro, usuario maestro postgres, autoadministrado)."),
        ("Evidencia 03", "P7, P8 / Act. 5 y 8", "Seguridad RDS (KMS + Backups)", "Captura de RDS confirmando Cifrado: Habilitado (KMS), Copias automáticas: Habilitado, Puerto 5432 y Accesible públicamente: No."),
        ("Evidencia 04", "P1, P2, P3 / Act. 1 y 5", "Integración EC2 <-> RDS TLS", "Salida JSON en vivo de /api/aws/estado/ vía API Gateway mostrando PostgreSQL 18.3 con TLS (sslmode=require)."),
        ("Evidencia 05", "P6 / Act. 4", "API Gateway Rate Limiting (429)", "Prueba de ráfaga real contra https://ozp0ipskkf.execute-api.us-east-1.amazonaws.com/prod/api/aws/rate-limit-test/ (5 x 200 OK -> 5 x 429 Too Many Requests)."),
        ("Evidencia 06", "P3, P7 / Act. 6", "Amazon S3 + Presigned URLs", "Generación de URL Prefirmada AWS4-HMAC-SHA256 sobre el bucket petcare-eva4-static-media-2026-047602603714-us-east-1-an."),
        ("Evidencia 07", "P4 / Act. 3", "Criptografía y Hash PBKDF2", "Desglose real del hash pbkdf2_sha256$870000$<salt>$<digest> en PostgreSQL y demostración de Salt único."),
        ("Evidencia 08", "P8 / Act. 7", "Amazon CloudWatch Alarma CPU", "Captura de configuración de alarma CPUUtilization sobre la instancia eva3_petcare (i-0987fd370228da4bc)."),
        ("Evidencia 09", "P8 / Act. 8", "AWS Lambda + IAM LabRole", "Captura de creación de la función Lambda PetCare-RDS-Backup-7h en Python 3.12."),
        ("Evidencia 10", "P8 / Act. 8", "Trigger EventBridge Cada 7 Horas", "Captura del diagrama de la función Lambda conectada al desencadenador EventBridge (rate(7 hours))."),
        ("Evidencia 11", "P8 / Act. 8", "Snapshots RDS Creándose y Disponibles", "Captura de RDS -> Instantáneas manuales mostrando los 2 snapshots generados por la Lambda (-7h-auto-) en estado Disponible (Completado)."),
        ("Evidencia 12", "P1..P8 / Act. 1..6", "Suite Automatizada SAST/DAST/API", "Ejecución en servidor de las 9 pruebas automatizadas (python manage.py test -> OK)."),
    ]
    tbl_idx = doc.add_table(rows=len(evidencias_index), cols=4)
    tbl_idx.style = 'Table Grid'
    tbl_idx.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row_vals in enumerate(evidencias_index):
        for j, val in enumerate(row_vals):
            c_p = tbl_idx.rows[i].cells[j].paragraphs[0]
            run = c_p.add_run(val)
            run.font.size = Pt(9)
            if i == 0 or j == 0:
                run.bold = True
    doc.add_paragraph()

    # ==================== SECCIÓN DE EVIDENCIAS GRÁFICAS Y PRÁCTICAS NUMERADAS ====================
    doc.add_heading("Anexo Principal: Evidencias Numeradas de Infraestructura AWS y Seguridad", level=1)

    add_evidence_image(
        doc,
        ev_dir / 'evidencia_01_arquitectura_aws.jpg',
        "Evidencia 01 — Arquitectura Distribuida Obligatoria en AWS (Separación de Capas)",
        "Arquitectura implementada: EC2 Frontend (3.230.130.63), Amazon API Gateway con Rate Limit (ozp0ipskkf), "
        "EC2 Backend DRF (98.85.49.169), Amazon RDS PostgreSQL 18.3, Amazon S3 y AWS Lambda + EventBridge cada 7 horas.",
        width_inches=3.6,
    )

    add_evidence_image(
        doc,
        ev_dir / 'evidencia_02_rds_creacion.jpg',
        "Evidencia 02 — Configuración y Dimensionamiento de Amazon RDS PostgreSQL",
        "Creación de la instancia RDS PostgreSQL (db.t4g.micro, usuario maestro postgres, administración de credenciales y vinculación con EC2).",
        width_inches=6.0,
    )

    add_evidence_image(
        doc,
        ev_dir / 'evidencia_03_rds_cifrado_kms_y_backups.png',
        "Evidencia 03 — Verificación de Cifrado en Reposo (KMS), Puerto 5432 y Respaldos Automáticos en RDS",
        "Tabla de configuración de RDS PostgreSQL 18.3 acreditando: Cifrado = Habilitado, Copias de seguridad automáticas = Habilitado, "
        "Accesible públicamente = No, Puerto = 5432 y VPC = vpc-01187b869943ea470.",
        width_inches=6.0,
    )

    doc.add_heading("Evidencia 04 — Telemetría JSON en Vivo vía API Gateway (Conectividad EC2 Backend <-> RDS TLS <-> S3)", level=2)
    doc.add_paragraph(
        "Respuesta real obtenida desde https://ozp0ipskkf.execute-api.us-east-1.amazonaws.com/prod/api/aws/estado/:"
    )
    add_code_block(
        doc,
        '{\n'
        '  "1_ec2_frontend": { "estado": "ACTIVO", "url": "http://3.230.130.63/" },\n'
        '  "2_ec2_backend": { "estado": "ACTIVO", "framework": "Django 5 + DRF + Gunicorn + Nginx" },\n'
        '  "3_rds_postgresql": {\n'
        '    "estado": "CONECTADO",\n'
        '    "version_motor": "PostgreSQL 18.3 on aarch64-unknown-linux-gnu",\n'
        '    "endpoint_host": "petcare-rds-postgres.cdsudpkituru.us-east-1.rds.amazonaws.com",\n'
        '    "puerto": "5432",\n'
        '    "instancia_separada_rds": true,\n'
        '    "cifrado_en_transito_tls": "TLS activo (sslmode=require)",\n'
        '    "cifrado_en_reposo_kms": "AWS KMS AES-256 habilitado al crear la instancia RDS",\n'
        '    "registros_persistidos": { "usuarios": 5, "profesionales": 3, "tutores": 3, "mascotas": 4, "citas_medicas": 4, "fichas_clinicas": 2, "controles_vacunas": 4 }\n'
        '  },\n'
        '  "4_amazon_s3": {\n'
        '    "bucket": "petcare-eva4-static-media-2026-047602603714-us-east-1-an",\n'
        '    "cifrado_en_reposo": "SSE-S3 (AES256)",\n'
        '    "block_public_access": "Activado (Block all public access = ON)"\n'
        '  },\n'
        '  "5_api_gateway": {\n'
        '    "invoke_url": "https://ozp0ipskkf.execute-api.us-east-1.amazonaws.com/prod",\n'
        '    "rate_limit_objetivo": "Rate: 2 solicitudes/segundo | Burst (Ráfaga): 5 solicitudes"\n'
        '  }\n'
        '}'
    )

    doc.add_heading("Evidencia 05 — Comprobación Práctica de Rate Limiting / Throttling en Amazon API Gateway (200 OK -> 429)", level=2)
    doc.add_paragraph(
        "Ejecución del script scripts/probar_rate_limit.py directamente contra la URL de invocación de Amazon API Gateway:"
    )
    add_code_block(
        doc,
        "========================================================================================\n"
        "  PETCARE EVA 4 — PRUEBA DE RATE LIMITING / THROTTLING (API GATEWAY & DRF)\n"
        "========================================================================================\n"
        "Endpoint evaluado : https://ozp0ipskkf.execute-api.us-east-1.amazonaws.com/prod/api/aws/rate-limit-test/\n"
        "Total solicitudes : 10 peticiones consecutivas en ráfaga\n"
        "----------------------------------------------------------------------------------------\n"
        "#    | Código HTTP              | Latencia   | Detalle de Respuesta\n"
        "----------------------------------------------------------------------------------------\n"
        "1    | 200 OK (Permitida)       | 111 ms     | 200 OK — Solicitud #1/5 procesada dentro del\n"
        "2    | 200 OK (Permitida)       | 94 ms      | 200 OK — Solicitud #2/5 procesada dentro del\n"
        "3    | 200 OK (Permitida)       | 120 ms     | 200 OK — Solicitud #3/5 procesada dentro del\n"
        "4    | 200 OK (Permitida)       | 40 ms      | 200 OK — Solicitud #4/5 procesada dentro del\n"
        "5    | 200 OK (Permitida)       | 33 ms      | 200 OK — Solicitud #5/5 procesada dentro del\n"
        "6    | 429 Too Many Requests    | 33 ms      | BLOQUEADO POR THROTTLING: Solicitud bloqueada\n"
        "7    | 429 Too Many Requests    | 37 ms      | BLOQUEADO POR THROTTLING: Solicitud bloqueada\n"
        "8    | 429 Too Many Requests    | 36 ms      | BLOQUEADO POR THROTTLING: Solicitud bloqueada\n"
        "9    | 429 Too Many Requests    | 11 ms      | BLOQUEADO POR THROTTLING: Solicitud bloqueada\n"
        "10   | 429 Too Many Requests    | 35 ms      | BLOQUEADO POR THROTTLING: Solicitud bloqueada\n"
        "----------------------------------------------------------------------------------------\n"
        "RESUMEN: 5 solicitudes aceptadas (200 OK) | 5 solicitudes bloqueadas (429 Too Many Requests)\n"
        "========================================================================================"
    )

    doc.add_heading("Evidencia 06 — Seguridad del Bucket Amazon S3 y URL Prefirmada (AWS4-HMAC-SHA256)", level=2)
    add_code_block(
        doc,
        '{\n'
        '  "actividad": "Actividad 6 — Seguridad del Bucket Amazon S3",\n'
        '  "bucket_name": "petcare-eva4-static-media-2026-047602603714-us-east-1-an",\n'
        '  "cifrado_en_reposo": "SSE-S3 (AES256)",\n'
        '  "block_public_access": true,\n'
        '  "acceso_directo_publico_bloqueado": "https://petcare-eva4-static-media-2026-047602603714-us-east-1-an.s3.us-east-1.amazonaws.com/recetas/receta_ficha_clinica_thor_2026.pdf -> 403 AccessDenied",\n'
        '  "algoritmo_firma": "AWS4-HMAC-SHA256 (Signature Version 4)",\n'
        '  "expiracion_segundos": 900\n'
        '}'
    )

    doc.add_heading("Evidencia 07 — Protección de Contraseñas en PostgreSQL (PBKDF2-HMAC-SHA256 y Salt Único)", level=2)
    add_code_block(
        doc,
        '{\n'
        '  "actividad": "Actividad 3 — Protección de contraseñas y criptografía (PBKDF2 / Argon2)",\n'
        '  "tabla_postgresql": "users_customuser",\n'
        '  "almacenado_en_texto_plano": false,\n'
        '  "algoritmo": "pbkdf2_sha256",\n'
        '  "funcion_prf": "HMAC-SHA256 (Familia SHA-2 de 256 bits)",\n'
        '  "iteraciones": 870000,\n'
        '  "hashes_identicos_misma_clave": false\n'
        '}'
    )

    add_evidence_image(
        doc,
        ev_dir / 'evidencia_08_cloudwatch_alarma_cpu.png',
        "Evidencia 08 — Monitoreo y Configuración de Alarma en Amazon CloudWatch (CPUUtilization)",
        "Configuración de la alarma sobre la métrica CPUUtilization del espacio de nombres AWS/EC2 para la instancia "
        "eva3_petcare (i-0987fd370228da4bc) con período de evaluación de 5 minutos y límite estático.",
        width_inches=6.0,
    )

    add_evidence_image(
        doc,
        ev_dir / 'evidencia_09_lambda_config_iam.jpg',
        "Evidencia 09 — Creación de Función AWS Lambda (PetCare-RDS-Backup-7h) en Python 3.12",
        "Configuración de la función serverless en AWS Lambda utilizando el runtime Python 3.12 y el rol de ejecución LabRole de AWS Academy.",
        width_inches=6.0,
    )

    add_evidence_image(
        doc,
        ev_dir / 'evidencia_10_lambda_eventbridge_7h.png',
        "Evidencia 10 — Función AWS Lambda Vinculada al Trigger Amazon EventBridge (rate(7 hours))",
        "Diagrama en consola AWS de la función arn:aws:lambda:us-east-1:047602603714:function:PetCare-RDS-Backup-7h "
        "activada automáticamente cada 7 horas por Amazon EventBridge.",
        width_inches=6.0,
    )

    add_evidence_image(
        doc,
        ev_dir / 'evidencia_11_rds_snapshots_7h_disponibles.png',
        "Evidencia 11 — Snapshots de RDS PostgreSQL 18.3 Generados por la Función Lambda (Disponibles)",
        "Consola de Amazon RDS -> Instantáneas manuales mostrando los dos respaldos creados por la automatización cada 7 horas "
        "(petcare-rds-postgres-7h-auto-2026-11-23-03-46 y petcare-rds-postgres-7h-auto-2026-11-23-03-52) en estado Disponible (Completado).",
        width_inches=6.0,
    )

    doc.add_heading("Evidencia 12 — Ejecución de Suite de 9 Pruebas Automatizadas en Servidor (EVA 3 + EVA 4)", level=2)
    add_code_block(
        doc,
        "Creating test database for alias 'default'...\n"
        "Ran 9 tests in 10.656s\n"
        "OK — System check identified no issues (0 silenced)."
    )

    # ==================== CONTENIDO TEÓRICO-TÉCNICO Y BANCO DE PREGUNTAS ORALES ====================
    md_path = base_dir / 'INFORME_TECNICO_EVA4.md'
    if md_path.exists():
        lines = md_path.read_text(encoding='utf-8').splitlines()
        in_code = False
        table_rows = []

        def flush_table(rows):
            if not rows:
                return
            clean = [r for r in rows if not all(set(c.strip()) <= set('-: ') for c in r)]
            if not clean:
                return
            cols = max(len(r) for r in clean)
            tbl = doc.add_table(rows=len(clean), cols=cols)
            tbl.style = 'Table Grid'
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            for i, row_data in enumerate(clean):
                for j, val in enumerate(row_data):
                    if j < cols:
                        cell_p = tbl.rows[i].cells[j].paragraphs[0]
                        run = cell_p.add_run(val.replace('**', '').replace('`', '').strip())
                        run.font.size = Pt(9.5)
                        if i == 0:
                            run.bold = True
            doc.add_paragraph()

        for line in lines:
            if line.strip().startswith('```'):
                if table_rows:
                    flush_table(table_rows)
                    table_rows = []
                in_code = not in_code
                continue

            if in_code:
                add_code_block(doc, line)
                continue

            if line.strip().startswith('|') and line.strip().endswith('|'):
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                table_rows.append(cells)
                continue
            else:
                if table_rows:
                    flush_table(table_rows)
                    table_rows = []

            if line.startswith('# ') or line.strip().startswith('!['):
                continue
            elif line.startswith('## '):
                doc.add_heading(line[3:].strip(), level=1)
            elif line.startswith('### '):
                doc.add_heading(line[4:].strip(), level=2)
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                txt = line.strip()[2:].replace('**', '').replace('`', '')
                doc.add_paragraph(txt, style='List Bullet')
            elif line.strip():
                txt = line.strip().replace('**', '').replace('`', '')
                doc.add_paragraph(txt)

        if table_rows:
            flush_table(table_rows)

    out_path = base_dir / 'Informe_Tecnico_EVA4_PetCare_Angel_Lara.docx'
    doc.save(out_path)
    print(f"[OK] Informe Word con capturas de evidencia generado en: {out_path}")


if __name__ == '__main__':
    build_docx()
