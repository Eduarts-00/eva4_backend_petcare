"""
Generador del Informe Técnico Oficial en formato Microsoft Word (.docx)
para la Evaluación N.º 4 de Programación Backend (PetCare — Arquitectura AWS, Integración y Seguridad).
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def build_docx():
    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    # Portada
    title = doc.add_Paragraph() if hasattr(doc, 'add_Paragraph') else doc.add_paragraph()
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
    r2.font.size = Pt(16)
    r2.font.color.rgb = RGBColor(30, 58, 138)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.LEFT
    meta.add_run("Estudiante: ").bold = True
    meta.add_run("Angel Eduardo Lara Manriquez (Sección IEC-N4-C2)\n")
    meta.add_run("Docente: ").bold = True
    meta.add_run("Marcelo Alvarado Aravena\n")
    meta.add_run("Repositorio GitHub EVA 4: ").bold = True
    meta.add_run("https://github.com/Eduarts-00/eva4_backend_petcare.git\n")
    meta.add_run("Instancia 2 — EC2 Frontend Desacoplado: ").bold = True
    meta.add_run("http://3.230.130.63/\n")
    meta.add_run("Instancia 1 — EC2 Backend DRF (HTTPS): ").bold = True
    meta.add_run("https://petcaree.duckdns.org/ (98.85.49.169)\n")
    meta.add_run("Amazon API Gateway (Rate Limit 2 req/s, Burst 5): ").bold = True
    meta.add_run("https://ozp0ipskkf.execute-api.us-east-1.amazonaws.com/prod\n")
    meta.add_run("Amazon RDS PostgreSQL 18.3 (TLS + KMS): ").bold = True
    meta.add_run("petcare-rds-postgres.cdsudpkituru.us-east-1.rds.amazonaws.com:5432\n")
    meta.add_run("Amazon S3 Bucket (SSE-S3 + Block Public Access): ").bold = True
    meta.add_run("petcare-eva4-static-media-2026-047602603714-us-east-1-an\n")

    # Leer INFORME_TECNICO_EVA4.md y volcar secciones estructuradas
    base_dir = Path(__file__).resolve().parent.parent
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
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.3)
                r_code = p.add_run(line)
                r_code.font.name = 'Consolas'
                r_code.font.size = Pt(9)
                continue

            if line.strip().startswith('|') and line.strip().endswith('|'):
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                table_rows.append(cells)
                continue
            else:
                if table_rows:
                    flush_table(table_rows)
                    table_rows = []

            if line.startswith('# '):
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
    print(f"[OK] Informe Word generado en: {out_path}")


if __name__ == '__main__':
    build_docx()
