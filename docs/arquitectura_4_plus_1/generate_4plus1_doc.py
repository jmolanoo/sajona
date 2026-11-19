"""Generador del Documento Profesional de Arquitectura 4+1 (SAJONA).

Estrictamente monocromático (Blanco #FFFFFF y Negro #000000), formato académico.
"""

import subprocess
from pathlib import Path
import pymupdf
from PIL import Image
import docx
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

BASE = Path("/home/molano/sajona")
DIAGRAMS_PNG = BASE / "docs/diagrams/png"
OUT_DIR = BASE / "docs/arquitectura_4_plus_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOCX_PATH = OUT_DIR / "SAJONA_Documento_Arquitectura_4_mas_1.docx"
PDF_PATH = OUT_DIR / "SAJONA_Documento_Arquitectura_4_mas_1.pdf"

BLACK = RGBColor(0x00, 0x00, 0x00)
FONT_NAME = "Liberation Serif"
FONT_SANS = "Liberation Sans"


def set_cell_margins(cell, top=90, bottom=90, left=130, right=130):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_bw_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '<w:left w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        '<w:right w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        "</w:tblBorders>"
    )
    tblPr.append(borders)


def set_row_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def set_row_header(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))


def add_field(run, field_text: str):
    fldChar1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
    instrText = parse_xml(r'<w:instrText %s xml:space="preserve"> %s </w:instrText>' % (nsdecls("w"), field_text))
    fldChar2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
    fldChar3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)


def configure_styles(doc: Document):
    normal = doc.styles["Normal"]
    normal.font.name = FONT_NAME
    normal.font.size = Pt(11)
    normal.font.color.rgb = BLACK
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(6)

    for level, size, before, after in (
        ("Title", 22, 12, 8),
        ("Heading 1", 15, 16, 6),
        ("Heading 2", 12.5, 12, 4),
        ("Heading 3", 11, 8, 3),
    ):
        st = doc.styles[level]
        st.font.name = FONT_SANS
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = BLACK
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True


def add_header_footer(doc: Document):
    sec = doc.sections[0]
    sec.top_margin = Inches(0.9)
    sec.bottom_margin = Inches(0.85)
    sec.left_margin = Inches(0.95)
    sec.right_margin = Inches(0.95)
    sec.different_first_page_header_footer = True

    hdr = sec.header.paragraphs[0]
    hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_h = hdr.add_run("SAJONA ADE — Documento de Arquitectura de Software (Modelo 4+1)")
    r_h.font.name = FONT_SANS
    r_h.font.size = Pt(8.5)
    r_h.font.color.rgb = BLACK

    ftr = sec.footer.paragraphs[0]
    ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = ftr.add_run("Universidad Surcolombiana (USCO) — Ingeniería de Software   |   Página ")
    r1.font.name = FONT_SANS
    r1.font.size = Pt(8.5)
    r1.font.color.rgb = BLACK
    r_pg = ftr.add_run()
    r_pg.font.name = FONT_SANS
    r_pg.font.size = Pt(8.5)
    r_pg.font.color.rgb = BLACK
    add_field(r_pg, "PAGE")
    r2 = ftr.add_run(" de ")
    r2.font.name = FONT_SANS
    r2.font.size = Pt(8.5)
    r2.font.color.rgb = BLACK
    r_tot = ftr.add_run()
    r_tot.font.name = FONT_SANS
    r_tot.font.size = Pt(8.5)
    r_tot.font.color.rgb = BLACK
    add_field(r_tot, "NUMPAGES")


def add_p(doc: Document, text: str = "", bold_prefix: str = "", align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = FONT_NAME
        rb.font.size = Pt(11)
        rb.font.color.rgb = BLACK
    if text:
        r = p.add_run(text)
        r.font.name = FONT_NAME
        r.font.size = Pt(11)
        r.font.color.rgb = BLACK
    return p


def add_bullets(doc: Document, items: list[tuple[str, str]]):
    for label, desc in items:
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(3)
        if label:
            rl = p.add_run(label + " ")
            rl.bold = True
            rl.font.name = FONT_NAME
            rl.font.size = Pt(10.5)
            rl.font.color.rgb = BLACK
        rd = p.add_run(desc)
        rd.font.name = FONT_NAME
        rd.font.size = Pt(10.5)
        rd.font.color.rgb = BLACK


def add_numbered(doc: Document, items: list[tuple[str, str]]):
    for label, desc in items:
        p = doc.add_paragraph(style="List Number")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(3)
        if label:
            rl = p.add_run(label + " ")
            rl.bold = True
            rl.font.name = FONT_NAME
            rl.font.size = Pt(10.5)
            rl.font.color.rgb = BLACK
        rd = p.add_run(desc)
        rd.font.name = FONT_NAME
        rd.font.size = Pt(10.5)
        rd.font.color.rgb = BLACK


def add_bw_table(doc: Document, headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None, caption: str | None = None):
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.keep_with_next = True
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(3)
        rc = cp.add_run(caption)
        rc.bold = True
        rc.font.name = FONT_SANS
        rc.font.size = Pt(9.5)
        rc.font.color.rgb = BLACK

    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_bw_borders(tbl)

    hdr_row = tbl.rows[0]
    set_row_header(hdr_row)
    set_row_cant_split(hdr_row)
    for idx, text in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(cell, top=100, bottom=100, left=110, right=110)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        r = p.add_run(text)
        r.bold = True
        r.font.name = FONT_SANS
        r.font.size = Pt(9.5)
        r.font.color.rgb = BLACK
        if col_widths:
            cell.width = Inches(col_widths[idx])

    for r_i, row_data in enumerate(rows):
        row = tbl.rows[r_i + 1]
        set_row_cant_split(row)
        for c_i, val in enumerate(row_data):
            cell = row.cells[c_i]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            set_cell_margins(cell, top=80, bottom=80, left=110, right=110)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.08
            r = p.add_run(val)
            r.font.name = FONT_NAME
            r.font.size = Pt(9.5)
            r.font.color.rgb = BLACK
            if col_widths:
                cell.width = Inches(col_widths[c_i])

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)


def add_diagram(doc: Document, filename: str, fig_num: str, title: str, explanation: str):
    img_path = DIAGRAMS_PNG / filename
    with Image.open(img_path) as im:
        px_w, px_h = im.size
    max_w = 6.35
    max_h = 6.8
    aspect = px_h / px_w
    width = max_w
    height = width * aspect
    if height > max_h:
        height = max_h
        width = height / aspect

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.keep_with_next = True
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after = Pt(3)
    p_img.add_run().add_picture(str(img_path), width=Inches(width), height=Inches(height))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(6)
    rc = p_cap.add_run(f"{fig_num}. {title}")
    rc.bold = True
    rc.italic = True
    rc.font.name = FONT_SANS
    rc.font.size = Pt(9.5)
    rc.font.color.rgb = BLACK

    if explanation:
        add_p(doc, explanation)


def build_cover(doc: Document):
    for text, size, bold, space in (
        ("UNIVERSIDAD SURCOLOMBIANA", 15, True, 4),
        ("FACULTAD DE INGENIERÍA — PROGRAMA DE INGENIERÍA DE SOFTWARE", 11.5, True, 28),
        ("DOCUMENTO DE ARQUITECTURA DE SOFTWARE (MODELO 4+1)", 20, True, 10),
        ("PROYECTO SAJONA: APLICACIÓN WEB PROGRESIVA (PWA) MOBILE-FIRST Y OFFLINE-FIRST PARA CONTROL Y TRAZABILIDAD DE CANNABIS MEDICINAL", 13, True, 24),
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(space)
        r = p.add_run(text)
        r.font.name = FONT_SANS
        r.font.size = Pt(size)
        r.bold = bold
        r.font.color.rgb = BLACK

    add_bw_table(
        doc,
        ["Atributo Institucional y del Proyecto", "Especificación Oficial"],
        [
            ["Sistema de Información", "SAJONA PWA — Trazabilidad Agrícola por Lotes (TRL-6)"],
            ["Empresa Cliente / Propietario del Dominio", "SAJONA ADE (NIT 900905923)"],
            ["Institución Académica", "Universidad Surcolombiana (USCO) — Programa de Ingeniería de Software"],
            ["Equipo de Ingeniería (Co-Desarrollo Horizontal)", "Danna Nerieth Palencia  |  Jairo Molano Salgado"],
            ["Docente Supervisor y Product Owner", "Ing. Eduardo Martínez Vidal"],
            ["Modelo de Documentación Arquitectónica", "Modelo de Vistas 4+1 de Philippe Kruchten (1995)"],
            ["Versión y Fecha de Emisión", "Versión 1.0 — 19 de noviembre de 2026"],
        ],
        col_widths=[2.5, 4.0],
    )

    p_place = doc.add_paragraph()
    p_place.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_place.paragraph_format.space_before = Pt(40)
    r_pl = p_place.add_run("Neiva, Huila — Colombia\nNoviembre de 2026")
    r_pl.font.name = FONT_SANS
    r_pl.font.size = Pt(11)
    r_pl.bold = True
    r_pl.font.color.rgb = BLACK

    doc.add_page_break()


def build_toc(
    doc: Document,
    toc_pages: dict[str, int] | None = None,
    fig_pages: dict[str, int] | None = None,
    tbl_pages: dict[str, int] | None = None,
):
    toc_entries = [
        (1, "1. Introducción"),
        (1, "2. Propósito y Alcance"),
        (1, "3. Contexto del Sistema"),
        (1, "4. Antecedentes, Auditoría e Ingeniería Inversa del Proyecto Existente"),
        (1, "5. Objetivos Arquitectónicos"),
        (1, "6. Requisitos Arquitectónicamente Significativos (ASR)"),
        (1, "7. Restricciones y Decisiones Tecnológicas"),
        (1, "8. Descripción General de la Arquitectura"),
        (1, "9. Vista Lógica"),
        (2, "9.1 Modelo Entidad-Relación Unificado"),
        (2, "9.2 Clases de Dominio e Invariantes"),
        (2, "9.3 Componentes Lógicos y Subdominios"),
        (1, "10. Vista de Procesos"),
        (2, "10.1 Flujo Agronómico Completo por Lote"),
        (2, "10.2 Sincronización Offline-First e Idempotencia"),
        (2, "10.3 Concurrencia Optimista y Resolución de Conflictos"),
        (1, "11. Vista de Desarrollo o Implementación"),
        (1, "12. Vista Física o de Despliegue"),
        (1, "13. Escenarios o Casos de Uso (+1)"),
        (1, "14. Estrategia Offline-First"),
        (1, "15. Persistencia y Sincronización"),
        (1, "16. Seguridad"),
        (1, "17. Integraciones y Comunicación entre Componentes"),
        (1, "18. Decisiones Arquitectónicas y sus Justificaciones"),
        (1, "19. Estrategia de Pruebas y Validación Arquitectónica"),
        (1, "20. Consideraciones de Rendimiento, Escalabilidad y Mantenibilidad"),
        (1, "21. Conclusiones"),
        (1, "22. Referencias Bibliográficas"),
        (1, "23. Anexos Técnicos"),
    ]

    h = doc.add_heading("Tabla de Contenido", level=1)
    h.paragraph_format.space_before = Pt(0)
    h.paragraph_format.space_after = Pt(8)

    for lvl, title in toc_entries:
        pg = str(toc_pages.get(title, "00")) if toc_pages else "00"
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.0 if lvl == 1 else 0.28)
        p.paragraph_format.space_before = Pt(2.5 if lvl == 1 else 1)
        p.paragraph_format.space_after = Pt(2 if lvl == 1 else 1)
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.tab_stops.add_tab_stop(
            Inches(6.55), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
        )
        r_t = p.add_run(title)
        r_t.font.name = FONT_SANS if lvl == 1 else FONT_NAME
        r_t.font.size = Pt(10 if lvl == 1 else 9.5)
        r_t.bold = lvl == 1
        r_t.font.color.rgb = BLACK

        r_tab = p.add_run("\t")
        r_tab.font.name = FONT_NAME
        r_tab.font.size = Pt(9.5)
        r_tab.font.color.rgb = BLACK

        r_p = p.add_run(pg)
        r_p.font.name = FONT_SANS if lvl == 1 else FONT_NAME
        r_p.font.size = Pt(10 if lvl == 1 else 9.5)
        r_p.bold = lvl == 1
        r_p.font.color.rgb = BLACK

    doc.add_page_break()

    fig_entries = [
        ("Figura 1", "Figura 1. Diagrama de Contexto del Sistema SAJONA PWA"),
        ("Figura 2", "Figura 2. Modelo Entidad-Relación Unificado de SAJONA (18 Tablas)"),
        ("Figura 3", "Figura 3. Diagrama de Clases del Núcleo de Dominio (sajona.domain)"),
        ("Figura 4", "Figura 4. Diagrama de Componentes Lógicos y Subdominios Funcionales"),
        ("Figura 5", "Figura 5. Diagrama de Actividades del Ciclo Productivo Unificado por Lote"),
        ("Figura 6", "Figura 6. Diagrama de Secuencia de Escritura Offline, Push Idempotente y Pull Delta"),
        ("Figura 7", "Figura 7. Diagrama de Secuencia de Detección y Resolución de Conflictos Concurrentes"),
        ("Figura 8", "Figura 8. Arquitectura en Capas Estricta del Backend y Reglas de Dependencia"),
        ("Figura 9", "Figura 9. Diagrama de Paquetes y Módulos del Sistema (Frontend PWA y Backend)"),
        ("Figura 10", "Figura 10. Diagrama de Despliegue Físico en VPS con Docker Compose y Túnel TLS 1.3"),
        ("Figura 11", "Figura 11. Diagrama de Casos de Uso por Perfil RBAC del Sistema SAJONA PWA"),
        ("Figura 12", "Figura 12. Escenario +1: Flujo End-to-End de Operario Sin Conectividad y Recuperación"),
    ]
    tbl_entries = [
        ("Tabla 1", "Tabla 1. Resumen de brechas y defectos corregidos tras la ingeniería inversa."),
        ("Tabla 2", "Tabla 2. Requisitos Arquitectónicamente Significativos y métricas verificadas."),
        ("Tabla 3", "Tabla 3. Especificación de contenedores desplegados en producción."),
        ("Tabla 4", "Tabla 4. Registro de Decisiones Arquitectónicas (ADR-001 a ADR-005)."),
        ("Tabla 5", "Tabla 5. Consolidado real de validación arquitectónica y pruebas ejecutadas."),
        ("Tabla 6", "Tabla 6. Inventario de endpoints implementados y documentados en OpenAPI."),
    ]

    hf = doc.add_heading("Índice de Figuras y Tablas", level=1)
    hf.paragraph_format.space_before = Pt(0)
    hf.paragraph_format.space_after = Pt(6)

    for key, label in fig_entries + tbl_entries:
        source_map = fig_pages if key.startswith("Figura") else tbl_pages
        pg = str(source_map.get(label, "00")) if source_map else "00"
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1.5)
        p.paragraph_format.space_after = Pt(1.5)
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.tab_stops.add_tab_stop(
            Inches(6.55), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
        )
        r_l = p.add_run(label)
        r_l.font.name = FONT_NAME
        r_l.font.size = Pt(9.5)
        r_l.font.color.rgb = BLACK
        p.add_run("\t").font.size = Pt(9.5)
        r_pg = p.add_run(pg)
        r_pg.font.name = FONT_SANS
        r_pg.font.size = Pt(9.5)
        r_pg.font.color.rgb = BLACK

    doc.add_page_break()


def populate_sections(doc: Document):
    # 1. Introducción
    doc.add_heading("1. Introducción", level=1)
    add_p(
        doc,
        "El presente documento especifica de manera integral la arquitectura de software implementada para la evolución del sistema SAJONA, concebido para el control, registro, seguimiento fenológico, trazabilidad por lotes y análisis químico postcosecha del cultivo de cannabis medicinal de la empresa SAJONA ADE (NIT 900905923). La documentación adopta el modelo de vistas 4+1 propuesto por Philippe Kruchten, articulando las vistas Lógica, de Procesos, de Desarrollo, Física y de Escenarios (+1) sobre la base real del software desarrollado, probado y desplegado.",
    )
    add_p(
        doc,
        "A diferencia de la concepción preliminar del proyecto orientada a formularios web dependientes de conectividad continua, la solución materializada corresponde a una Aplicación Web Progresiva (PWA) con diseño prioritario para teléfonos inteligentes (Mobile-First) y operación autónoma sin conexión a Internet (Offline-First). Esta arquitectura garantiza que operarios en invernaderos, casas malla y terrenos rurales puedan registrar cada etapa productiva sin pérdida ni duplicación de datos.",
    )

    # 2. Propósito y Alcance
    doc.add_heading("2. Propósito y Alcance", level=1)
    add_p(
        doc,
        "El propósito de este documento es establecer la referencia técnica verificable de la arquitectura de SAJONA para los equipos de ingeniería, aseguramiento de calidad, operación en VPS y evaluación académica en el Programa de Ingeniería de Software de la Universidad Surcolombiana. Cada componente, clase, tabla, contrato HTTP y diagrama descrito en estas secciones corresponde estrictamente a elementos implementados y validados.",
    )
    add_bullets(
        doc,
        [
            ("Dentro del alcance implementado:", "Autenticación segura con recuperación de contraseña y control de acceso basado en roles (RBAC); gestión de catálogos maestros (variedades, ubicaciones y complicaciones); ciclo agrícola unificado por lote en nueve módulos operativos (Propagación, Transplante a Bolsa, Planta Madre y Extracciones, Transplante a Campo, Plan de Control e Historia Clínica, Cosecha, Post Cosecha con % CBD y % THC, Bajas y Reportes en Excel/TXT/PDF); motor de sincronización Offline-First con IndexedDB, cola Outbox, detección y resolución de conflictos; bitácora de auditoría inmutable; y despliegue en contenedores Docker con proxy inverso y túnel TLS 1.3."),
            ("Fuera del alcance de la versión 1.0:", "Módulos contables, facturación electrónica, nómina, transformación industrial secundaria de aceites o extractos farmacéuticos, telemetría directa desde sensores IoT en hardware de campo e interoperabilidad automática con portales regulatorios gubernamentales externos."),
        ],
    )

    # 3. Contexto del Sistema
    doc.add_heading("3. Contexto del Sistema", level=1)
    add_p(
        doc,
        "SAJONA opera en un entorno agroindustrial regulado donde la trazabilidad genética y cuantitativa de cada lote de material vegetal determina el cumplimiento sanitario y la toma de decisiones agronómicas. La empresa SAJONA ADE actúa como propietaria del proceso productivo, en articulación con el ecosistema regional del Huila (antecedentes de alianza con Flor Opita y SENA TecnoParque) y gremios agricultores dedicados a cultivos de valor agregado.",
    )
    add_diagram(
        doc,
        "fig01_contexto_sistema.png",
        "Figura 1",
        "Diagrama de Contexto del Sistema SAJONA PWA",
        "La Figura 1 ilustra la interacción de los cuatro perfiles de usuario con la PWA instalada en dispositivos móviles o de escritorio, la persistencia local en IndexedDB y la comunicación cifrada hacia la infraestructura Docker desplegada en la VPS.",
    )

    # 4. Antecedentes y Auditoría
    doc.add_heading("4. Antecedentes, Auditoría e Ingeniería Inversa del Proyecto Existente", level=1)
    add_p(
        doc,
        "Previo al diseño definitivo, se ejecutó una auditoría documental y visual exhaustiva sobre los quince artefactos heredados del repositorio histórico (2021 y 2026): análisis de requerimientos, historias de usuario CV-01 a CV-09 con wireframes incrustados, el documento Mockups_SAJONA.pdf (10 páginas), el modelo relacional modelo_pdf_sajona.pdf (12 tablas), la presentación Prediseno.pptx (14 diapositivas), el documento de Gobernanza y el diagnóstico de contexto.",
    )
    add_bw_table(
        doc,
        ["Hallazgo / Defecto Auditado", "Artefacto de Origen", "Impacto Técnico", "Resolución en la Nueva Arquitectura"],
        [
            ["post_cbd y post_thc como DECIMAL(1,2)", "modelo_pdf_sajona.pdf", "Imposibilita guardar concentraciones >= 1.00% (ej. 14.80% CBD).", "Corregido a NUMERIC(5,2) con validación de rango 0.00 a 100.00."],
            ["usr_password como VARCHAR(20)", "modelo_pdf_sajona.pdf", "Impide almacenar hashes seguros Argon2id/bcrypt (> 60 caracteres).", "Ampliado a VARCHAR(255) con hashing Argon2id exclusivo en servidor."],
            ["pm_fecha_esquejacion como NUMERIC y falta de FK usuario-funcionario", "modelo_pdf_sajona.pdf", "Consultas cronológicas inválidas y desacoplamiento de identidad.", "Tipado a DATE, FK explícita usuario.funcionario_id y correo VARCHAR(255)."],
            ["FK invertida transplante.tp_pm_id -> planta_madre", "modelo_pdf_sajona.pdf", "Bloquea trasplantes a bolsa previos al registro de planta madre.", "Vinculación directa de transplantes al lote (lote_id -> propagaciones.id)."],
            ["Divergencia flujo V1 (planta) vs V2 (lote) y omisiones de UI", "CV-01..09 y Mockups_SAJONA.pdf", "Pérdida de campos de terreno/surcos en Campo y ausencia de Plan de Control.", "Unificación por codigo_lote/UUID integrando Historia Clínica, Revisión y Catálogos."],
            ["Error aritmético y rotulado en modal Lote 30", "Mockups_SAJONA.pdf pág. 7 vs CV-09", "Confusión entre Número de Planta Madre y sumatoria (30+28 != 37).", "Adopción de semántica exacta de CV-09 con sumatorias calculadas en tiempo real."],
            ["Arquitectura online-only en Gobernanza", "Gobernanza (2026)", "Inoperabilidad en invernaderos y terrenos rurales sin señal móvil.", "Evolución justificada mediante ADR-002 hacia PWA Offline-First con IndexedDB."],
        ],
        col_widths=[1.6, 1.3, 1.7, 1.9],
        caption="Tabla 1. Resumen de brechas y defectos corregidos tras la ingeniería inversa.",
    )

    # 5. Objetivos Arquitectónicos
    doc.add_heading("5. Objetivos Arquitectónicos", level=1)
    add_bullets(
        doc,
        [
            ("Continuidad operativa sin conectividad:", "Garantizar el registro, consulta y exportación de información productiva aun cuando el dispositivo móvil pierda señal celular o Wi-Fi en campo."),
            ("Integridad y consistencia eventual verificable:", "Preservar el balance biológico por lote (bajas, supervivencia, rendimientos de secado) evitando duplicados y resolviendo conflictos concurrentes sin pérdida silenciosa de datos."),
            ("Mantenibilidad y separación estricta de capas:", "Mantener el núcleo de dominio libre de dependencias de frameworks mediante reglas verificadas automáticamente."),
            ("Seguridad y auditabilidad completa:", "Asegurar autenticación robusta, control granular RBAC, protección de almacenamiento local y trazabilidad append-only de todas las escrituras."),
        ],
    )

    # 6. ASR
    doc.add_heading("6. Requisitos Arquitectónicamente Significativos (ASR)", level=1)
    add_bw_table(
        doc,
        ["ID", "Atributo / Requisito", "Escenario y Umbral Cuantitativo", "Mecanismo de Verificación"],
        [
            ["ASR-01", "Operación Offline-First", "Creación, edición, cierre y reapertura de la PWA sin red con sincronización posterior íntegra.", "Pruebas Vitest con IndexedDB y Playwright E2E con Context.setOffline(true)."],
            ["ASR-02", "Rendimiento API", "Latencia p95 <= 500 ms y tasa de error < 1% en operaciones principales bajo carga nominal.", "Benchmark HTTP automatizado (p95 medido: 4.62 ms, 0 errores)."],
            ["ASR-03", "Auditabilidad Inmutable", "100% de escrituras online y offline registradas con usuario, fecha, resultado y correlation_id.", "Pruebas de integración sobre tabla audit_logs y volumen JSONL."],
            ["ASR-04", "Seguridad RBAC y Local", "0 contraseñas o hashes almacenados en navegador; rechazo 403 ante escalamiento de privilegios.", "Pruebas de integración RBAC y auditoría de sesión IndexedDB."],
            ["ASR-05", "Usabilidad y Accesibilidad", "Interfaz Mobile-First (>= 44 px táctil), WCAG 2.2 AA con 0 violaciones críticas.", "Auditoría automatizada con @axe-core/playwright en móvil y escritorio."],
            ["ASR-06", "Portabilidad y Despliegue", "Levantamiento completo desde cero con docker compose up en <= 10 min y respaldos verificados.", "Despliegue real en VPS + ejecución de backup.sh y restore_test.sh."],
        ],
        col_widths=[0.7, 1.4, 2.3, 2.1],
        caption="Tabla 2. Requisitos Arquitectónicamente Significativos y métricas verificadas.",
    )

    # 7. Restricciones y Decisiones Tecnológicas
    doc.add_heading("7. Restricciones y Decisiones Tecnológicas", level=1)
    add_p(
        doc,
        "El stack tecnológico se seleccionó considerando la infraestructura VPS disponible (Ubuntu 24.04 x86_64, 12 vCPU, 15 GiB RAM, firewall perimetral con puertos públicos restringidos a SSH) y las restricciones de contexto seguro exigidas por los Service Workers en navegadores modernos. Para el servidor se seleccionó Python 3.12 con FastAPI, SQLAlchemy 2 asíncrono y PostgreSQL 16.6; para el cliente PWA, React 18 con TypeScript en modo estricto, Tailwind CSS, Dexie.js sobre IndexedDB y Workbox (vite-plugin-pwa en modo injectManifest).",
    )

    # 8. Descripción General
    doc.add_heading("8. Descripción General de la Arquitectura", level=1)
    add_p(
        doc,
        "SAJONA implementa un patrón híbrido Cliente-Servidor Desacoplado Offline-First: el cliente PWA actúa como aplicación autónoma capaz de ejecutar reglas de cálculo, validar formularios, almacenar estado completo en IndexedDB y generar reportes locales (Excel, TXT, PDF), delegando al servidor FastAPI la autoridad transaccional definitiva, el control de versiones optimista, la resolución de idempotencia y la persistencia centralizada en PostgreSQL.",
    )

    # 9. Vista Lógica
    doc.add_heading("9. Vista Lógica", level=1)
    add_p(
        doc,
        "La Vista Lógica describe la descomposición estructural del dominio del problema: sus entidades persistentes, relaciones de integridad referencial, clases de dominio y módulos funcionales.",
    )
    doc.add_heading("9.1 Modelo Entidad-Relación Unificado", level=2)
    add_diagram(
        doc,
        "fig02_modelo_entidad_relacion.png",
        "Figura 2",
        "Modelo Entidad-Relación Unificado de SAJONA (18 Tablas)",
        "La Figura 2 muestra el esquema relacional corregido en PostgreSQL 16. Destacan las claves primarias UUIDv4 para creación offline sin colisiones, la FK explícita entre usuarios y funcionarios, la corrección a NUMERIC(5,2) en post_cosechas, las tablas catálogo (variedades, ubicaciones, tipos_complicacion) y las tablas de gobernanza (audit_logs, processed_mutations).",
    )
    doc.add_heading("9.2 Clases de Dominio e Invariantes", level=2)
    add_diagram(
        doc,
        "fig03_clases_dominio.png",
        "Figura 3",
        "Diagrama de Clases del Núcleo de Dominio (sajona.domain)",
        "Todas las entidades heredan de SyncMetadata (id, version, created_at, updated_at, deleted_at). Las reglas puras en rules.py garantizan el balance biológico de trasplantes, la protección contra bajas excedentes, la validez química de cannabinoides y la cronología fenológica.",
    )
    doc.add_heading("9.3 Componentes Lógicos y Subdominios", level=2)
    add_diagram(
        doc,
        "fig04_componentes_logicos.png",
        "Figura 4",
        "Diagrama de Componentes Lógicos y Subdominios Funcionales",
        "El sistema se organiza en cuatro bloques lógicos cohesivos: Seguridad y Gobernanza, Parámetros Maestros, Trazabilidad Agrícola por Lote (M1–M8) y Capacidades Transversales Offline-First (Motor de Sincronización y Reportes).",
    )

    # 10. Vista de Procesos
    doc.add_heading("10. Vista de Procesos", level=1)
    add_p(
        doc,
        "La Vista de Procesos detalla el comportamiento dinámico en tiempo de ejecución, la concurrencia entre dispositivos, la secuencia de sincronización asíncrona y la recuperación ante interrupciones de red.",
    )
    doc.add_heading("10.1 Flujo Agronómico Completo por Lote", level=2)
    add_diagram(
        doc,
        "fig05_actividades_ciclo_lote.png",
        "Figura 5",
        "Diagrama de Actividades del Ciclo Productivo Unificado por Lote",
        "Desde Propagación (1), el lote pasa a Transplante a Bolsa (2) donde se evalúa supervivencia; si la merma supera el 20% se emite alerta. Según Tipo de Lote, continúa hacia Ruta A (Planta Madre y derivación genética de nuevos lotes hijos) o Ruta B (Transplante a Campo, Plan de Control, Cosecha y Post Cosecha), con registro transversal de Bajas.",
    )
    doc.add_heading("10.2 Sincronización Offline-First e Idempotencia", level=2)
    add_diagram(
        doc,
        "fig06_secuencia_sync_offline.png",
        "Figura 6",
        "Diagrama de Secuencia de Escritura Offline, Push Idempotente y Pull Delta",
        "Toda escritura local ocurre en una transacción atómica sobre IndexedDB (actualizando entidad y cola outbox_mutations). Al recuperar señal, AuthContext renueva el token de acceso mediante una promesa única (mutex) y SyncEngine ejecuta POST /api/v1/sync/push en orden topológico causal seguido de GET /api/v1/sync/pull.",
    )
    doc.add_heading("10.3 Concurrencia Optimista y Resolución de Conflictos", level=2)
    add_diagram(
        doc,
        "fig07_secuencia_conflictos.png",
        "Figura 7",
        "Diagrama de Secuencia de Detección y Resolución de Conflictos Concurrentes",
        "Cuando dos dispositivos editan el mismo registro concurrentemente, el servidor compara base_version con la versión vigente en PostgreSQL. Al detectar desfase, responde con status='conflict' y el estado actual del servidor sin sobrescribir cambios, habilitando al usuario en SyncCenterModal para conservar su versión o aceptar la del servidor.",
    )

    # 11. Vista de Desarrollo
    doc.add_heading("11. Vista de Desarrollo o Implementación", level=1)
    add_p(
        doc,
        "La Vista de Desarrollo establece la organización estática del código fuente, los límites entre capas y las dependencias permitidas, tanto en el monolito modular del backend como en la PWA del frontend.",
    )
    add_diagram(
        doc,
        "fig08_capas_dependencias.png",
        "Figura 8",
        "Arquitectura en Capas Estricta del Backend y Reglas de Dependencia",
        "La regla de dependencia impone que sajona.domain no importe ningún módulo externo ni de capas superiores. Esta restricción se verifica automáticamente mediante import-linter (2 contratos cumplidos, 0 violaciones) junto con tipado estricto mypy --strict y complejidad ciclomática <= 10 con ruff.",
    )
    add_diagram(
        doc,
        "fig09_paquetes_modulos.png",
        "Figura 9",
        "Diagrama de Paquetes y Módulos del Sistema (Frontend PWA y Backend)",
        "En el frontend, las páginas (pages/) interactúan con la capa local db/ (Dexie + syncEngine) y componentes reutilizables (components/), desacoplando la UI del estado de la red. El acceso HTTP hacia /api/v1/* se encapsula en api/client.ts y se respalda por el Service Worker sw.ts.",
    )

    # 12. Vista Física
    doc.add_heading("12. Vista Física o de Despliegue", level=1)
    add_p(
        doc,
        "La solución se encuentra desplegada en la VPS Ubuntu 24.04 x86_64 mediante Docker Compose con cinco servicios contenedores en versiones fijas, usuarios sin privilegios de root, límites explícitos de CPU/RAM, endpoints de salud (/health) y aislamiento de red en dos capas.",
    )
    add_bullets(
        doc,
        [
            ("Aislamiento de Red (sajona-backend-net):", "Configurada con internal: true para impedir cualquier enrutamiento hacia Internet desde PostgreSQL (sajona-db) o desde el servicio automático de copias de seguridad (sajona-backup)."),
            ("Publicación Unificada y Contexto Seguro TLS 1.3:", "El proxy inverso Nginx 1.27.3 no-root atiende SPA y tráfico /api/* sobre un único origen HTTP interno (127.0.0.1:8088 -> 8080), enlazado mediante túnel cifrado saliente Cloudflare (sajona-tunnel) para satisfacer el requisito de contexto seguro HTTPS exigido por los Service Workers en navegadores móviles."),
            ("Persistencia en Volúmenes Nombrados:", "El estado de base de datos, los volcados gzip diarios (retención de 14 copias verificables) y la bitácora JSONL residen en volúmenes Docker independientes del ciclo de recreación de contenedores."),
        ],
    )
    add_diagram(
        doc,
        "fig10_despliegue_vps.png",
        "Figura 10",
        "Diagrama de Despliegue Físico en VPS con Docker Compose y Túnel TLS 1.3",
        "La red sajona-backend-net se configura con internal: true, aislando completamente a PostgreSQL (sajona-db) y al servicio de copias de seguridad (sajona-backup) de cualquier acceso externo. Únicamente sajona-proxy (Nginx 1.27.3 no-root) sirve la PWA y enruta /api/* hacia sajona-backend, exponiéndose mediante HTTPS TLS 1.3 a través de sajona-tunnel (cloudflared 2026.11.1).",
    )
    add_bw_table(
        doc,
        ["Servicio Docker", "Imagen Base Fija", "Usuario", "Red(es)", "Límites / Persistencia"],
        [
            ["sajona-db", "postgres:16.6-alpine", "postgres", "sajona-backend-net", "1.0 CPU, 512M RAM | Vol. sajona_pgdata"],
            ["sajona-backend", "python:3.12.7-slim", "sajona (UID 1001)", "backend-net + frontend-net", "1.0 CPU, 512M RAM | Vol. sajona_audit_logs"],
            ["sajona-backup", "postgres:16.6-alpine", "postgres", "sajona-backend-net", "0.25 CPU, 128M RAM | Vol. sajona_backups"],
            ["sajona-proxy", "nginx:1.27.3-alpine", "nginx (puerto 8080)", "sajona-frontend-net", "0.50 CPU, 256M RAM | Enlace 127.0.0.1:8088"],
            ["sajona-tunnel", "cloudflare/cloudflared:2026.11.1", "nonroot", "sajona-frontend-net", "0.25 CPU, 128M RAM | Terminación TLS 1.3"],
        ],
        col_widths=[1.1, 1.5, 1.1, 1.3, 1.5],
        caption="Tabla 3. Especificación de contenedores desplegados en producción.",
    )

    # 13. Escenarios (+1)
    doc.add_heading("13. Escenarios o Casos de Uso (+1)", level=1)
    add_p(
        doc,
        "La vista +1 valida la coherencia entre las vistas Lógica, de Procesos, de Desarrollo y Física mediante los casos de uso del negocio y el escenario arquitectónicamente significativo de operación en campo sin conectividad.",
    )
    add_bullets(
        doc,
        [
            ("Actores y Segregación de Funciones:", "Operario de Campo ejecuta capturas fenológicas (UC-02 a UC-08) y sincronización (UC-10) incluso sin señal; Jefe de Proyecto supervisa todo el ciclo y emite reportes (UC-09); Consulta accede en solo lectura; Administrador administra cuentas, parámetros y bitácora (UC-11)."),
            ("Escenario Crítico de Desconexión y Reapertura:", "Tras el primer inicio de sesión con red, el operario pierde cobertura en invernadero, registra lotes en IndexedDB, cierra completamente la PWA y vuelve a abrirla sin señal, verificando continuidad operativa, empuje automático y resolución explícita ante conflictos concurrentes."),
        ],
    )
    add_diagram(
        doc,
        "fig11_casos_uso.png",
        "Figura 11",
        "Diagrama de Casos de Uso por Perfil RBAC del Sistema SAJONA PWA",
        "Los casos de uso UC-01 a UC-11 delimitan exactamente las facultades de cada rol: Operario ejecuta registro en campo y sincronización; Jefe de Proyecto dirige el ciclo productivo y reportes; Consulta accede en solo lectura; Administrador gobierna usuarios, roles, parámetros y auditoría.",
    )
    add_diagram(
        doc,
        "fig12_escenario_offline_e2e.png",
        "Figura 12",
        "Escenario +1: Flujo End-to-End de Operario Sin Conectividad y Recuperación",
        "Este escenario articula simultáneamente el Service Worker (Fases 1 y 4), el motor IndexedDB + Outbox (Fases 2 y 3), el backend idempotente (Fase 5) y la resolución de conflictos optimista (Fase 6).",
    )

    # 14. Estrategia Offline-First
    doc.add_heading("14. Estrategia Offline-First", level=1)
    add_bullets(
        doc,
        [
            ("Web App Manifest y Service Worker (Workbox injectManifest):", "El archivo manifest.webmanifest configura display standalone, orientación portrait-primary e iconos PNG en 192x192 y 512x512 (estándar y maskable). El Service Worker sw.ts precachea los 14 artefactos del App Shell (HTML, CSS, JS fragmentado en chunks, iconos) y sirve /index.html como fallback de navegación ante cualquier ruta solicitada sin red, aplicando estrategia NetworkOnly para /api/* para impedir respuestas cacheadas engañosas."),
            ("Persistencia Estructurada en IndexedDB:", "La base local sajonadb (Dexie 4) replica las 11 tablas operativas y de catálogos, manteniendo un estado _local_sync_status ('synced' | 'pending' | 'conflict') en cada registro y la tabla outbox_mutations para escrituras diferidas."),
            ("Experiencia Mobile-First y Visibilidad de Estado:", "En pantallas menores a 768 px, los listados tabulares se transforman automáticamente en tarjetas táctiles apiladas y la navegación emplea una barra inferior fija más un cajón lateral completo. La cabecera exhibe permanentemente un indicador interactivo de conectividad y cantidad de pendientes o conflictos."),
            ("Exportación Local Sin Red:", "Los exportadores de Excel (.xlsx vía ExcelJS), Texto (.txt) y PDF (.pdf vía jsPDF + autoTable) se cargan por demanda (code splitting reduciendo el bundle principal a 376.14 kB) y permanecen precacheados por el Service Worker, operando 100% desde IndexedDB sin requerir servidor."),
        ],
    )

    # 15. Persistencia y Sincronización
    doc.add_heading("15. Persistencia y Sincronización", level=1)
    add_p(
        doc,
        "La consistencia entre dispositivos móviles y PostgreSQL descansa sobre cuatro garantías formales implementadas en syncEngine.ts y sync_service.py:",
    )
    add_numbered(
        doc,
        [
            ("Identidad UUIDv4 y Orden Topológico Causal:", "Los registros creados sin conexión reciben UUIDv4 en cliente, permitiendo encadenar propagaciones -> trasplantes -> cosechas -> postcosechas offline. Al sincronizar, las mutaciones se ordenan en el grafo causal desde catálogos hasta bajas."),
            ("Idempotencia Estricta (client_mutation_id):", "Cada operación encolada porta un client_mutation_id único. El backend lo persiste en processed_mutations tras aplicarlo; si un corte de red interrumpe la respuesta HTTP y el cliente reintenta con backoff exponencial (1.5s a 60s), el servidor devuelve status='duplicate' sin duplicar el registro."),
            ("Concurrencia Optimista (version):", "Toda mutación UPDATE o DELETE declara base_version. Si otro usuario modificó el registro en el ínterin, el servidor rechaza la sobrescritura automática y retorna status='conflict' con el registro vigente del servidor."),
            ("Pull Incremental Protegido:", "GET /api/v1/sync/pull?since=cursor descarga registros modificados y eliminados lógicamente (deleted_at != null), omitiendo en IndexedDB aquellos registros que mantienen mutaciones locales pendientes o en conflicto."),
        ],
    )

    # 16. Seguridad
    doc.add_heading("16. Seguridad", level=1)
    add_bullets(
        doc,
        [
            ("Criptografía de Credenciales:", "Las contraseñas se procesan en servidor con Argon2id (pwdlib) y se almacenan en VARCHAR(255). Jamás se almacenan contraseñas ni hashes en el navegador."),
            ("Sesiones Híbridas Seguras:", "En línea, el backend emite un JWT Bearer de vida corta (15 minutos, HS256) y un Refresh Token opaco rotatorio de un solo uso almacenado en cookie HttpOnly; SameSite=Lax; Secure (cuando HTTPS está activo). Para reapertura offline en campo, IndexedDB conserva únicamente el perfil público, permisos RBAC y una ventana de gracia limitada (offline_grace_until), renovando con mutex único al volver la red."),
            ("Autorización RBAC y Auditoría:", "Todos los endpoints REST y el motor /api/v1/sync/push exigen validación de permisos por rol (ADMIN, JEFE_PROYECTO, OPERARIO, CONSULTA). Cada mutación registra trazabilidad en audit_logs y archivo append-only audit.jsonl con X-Correlation-ID."),
            ("Endurecimiento de Red y Cabeceras:", "Nginx inyecta X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy y Permissions-Policy. Todos los contenedores ejecutan bajo usuarios no-root."),
        ],
    )

    # 17. Integraciones y Comunicación
    doc.add_heading("17. Integraciones y Comunicación entre Componentes", level=1)
    add_p(
        doc,
        "La comunicación cliente-servidor se articula mediante una API REST JSON versionada (/api/v1/*) documentada por OpenAPI en FastAPI. Toda petición transporta X-Correlation-ID y toda respuesta de error sigue un contrato uniforme {error: {code, message, correlation_id}}. El enrutamiento unificado a través de sajona-proxy bajo un único origen elimina fricciones CORS y protege cookies HttpOnly entre frontend y backend.",
    )

    # 18. Decisiones Arquitectónicas (ADRs)
    doc.add_heading("18. Decisiones Arquitectónicas y sus Justificaciones", level=1)
    add_bw_table(
        doc,
        ["ADR", "Decisión Adoptada", "Alternativa Descartada / Disposición Modificada", "Justificación y Consecuencia"],
        [
            ["ADR-001", "Unificación por Lote con UUIDv4 y corrección de tipos en esquema.", "Modelo ER de 2021 con INT secuenciales, DECIMAL(1,2) y tp_pm_id invertido.", "Evita fallos SQL en %CBD/%THC y permite crear cadenas completas sin conexión."],
            ["ADR-002", "PWA Mobile-First y Offline-First con IndexedDB y Outbox.", "Aplicación web tradicional dependiente de red (Gobernanza 2026).", "Apartamiento justificado: asegura operación continua en cultivos sin cobertura."],
            ["ADR-003", "Monolito modular de 4 capas (FastAPI) + React TS.", "Microservicios distribuidos.", "Reduce latencia de red interna y complejidad operativa manteniendo desacople por capas."],
            ["ADR-004", "Nginx no-root + Túnel cloudflared TLS 1.3 en Docker.", "Exposición HTTP directa sin certificado TLS.", "Contexto seguro obligatorio para registrar Service Workers e instalar la PWA en móviles."],
            ["ADR-005", "Refresh Token HttpOnly con mutex + sesión offline acotada.", "Tokens de larga vida en localStorage.", "Previene robo de sesiones por XSS sin sacrificar reapertura offline."],
        ],
        col_widths=[0.75, 1.85, 1.85, 2.05],
        caption="Tabla 4. Registro de Decisiones Arquitectónicas (ADR-001 a ADR-005).",
    )

    # 19. Estrategia de Pruebas
    doc.add_heading("19. Estrategia de Pruebas y Validación Arquitectónica", level=1)
    add_p(
        doc,
        "La arquitectura fue validada mediante una pirámide de pruebas automatizadas ejecutadas sobre el software real y la infraestructura desplegada:",
    )
    add_bw_table(
        doc,
        ["Nivel de Prueba", "Alcance Verificado", "Herramienta", "Resultado Observado"],
        [
            ["Unitarias Backend", "Reglas agronómicas puras (RN-01 a RN-06): supervivencia, bajas, secado, %CBD/%THC.", "pytest", "7 / 7 aprobadas (Dominio: entities/enums/exceptions 100%, rules 97%)."],
            ["Integración y Contrato API", "Auth, rotación refresh, RBAC 403, 11 entidades, sync idempotente, conflictos y OpenAPI.", "pytest + httpx ASGI", "6 / 6 aprobadas (13 / 13 totales en 5.66 s; Cobertura global: 83%)."],
            ["Estático y Dependencias", "Tipado estricto, complejidad ciclomática <= 10 y reglas de capas.", "mypy, ruff, import-linter", "0 errores en 27 archivos; 2 contratos de capas cumplidos."],
            ["Unitarias PWA / IndexedDB", "Cálculos cliente, cola Outbox en fake-indexeddb y resolución de conflictos.", "Vitest", "4 / 4 aprobadas en 433 ms (100%)."],
            ["E2E Navegador Real HTTPS", "Login, SW activo, creación offline, cierre/reapertura sin red, auto-sync, conflicto concurrente y vistas móvil/escritorio.", "Playwright Chromium", "1 / 1 flujo completo aprobado (13.7 s caso / 14.4 s suite) sobre HTTPS real."],
            ["Accesibilidad y Seguridad", "Auditoría WCAG en Login/Dashboard y escaneo de dependencias.", "@axe-core + npm audit", "0 violaciones críticas; 0 vulnerabilidades altas/críticas en runtime."],
            ["Rendimiento y Respaldos", "50 peticiones GET /propagacion y respaldo/verificación PostgreSQL.", "Benchmark Python + pg_dump", "p50 = 3.93 ms, p95 = 4.62 ms (0 errores); 20 sentencias CREATE TABLE verificadas."],
        ],
        col_widths=[1.3, 2.2, 1.3, 1.7],
        caption="Tabla 5. Consolidado real de validación arquitectónica y pruebas ejecutadas.",
    )

    # 20. Rendimiento, Escalabilidad y Mantenibilidad
    doc.add_heading("20. Consideraciones de Rendimiento, Escalabilidad y Mantenibilidad", level=1)
    add_bullets(
        doc,
        [
            ("Rendimiento Móvil y Servidor:", "El uso de importación dinámica para librerías pesadas de exportación (exceljs, jspdf) mantiene el paquete principal de arranque en 376.14 kB (109.65 kB gzip). En servidor, FastAPI asíncrono sobre 2 workers Uvicorn y PostgreSQL 16 alcanzó un p95 de 4.62 ms, ampliamente por debajo de la meta de 500 ms."),
            ("Escalabilidad:", "La paginación/pull incremental por cursor temporal evita transferencias masivas conforme crecen los lotes históricos. Si la concurrencia futura exigiera escalado horizontal, la ausencia de estado en sesión de aplicación (respaldada por PostgreSQL y refresh tokens compartidos) permite replicar sajona-backend detrás de sajona-proxy."),
            ("Mantenibilidad:", "El código aplica tipado estricto en Python y TypeScript, funciones cohesivas de complejidad ciclomática <= 10 y una arquitectura simétrica orientada a especificaciones de entidad (ENTITY_SPECS en backend y ResponsiveRecordsView en frontend) que evita duplicación de lógica."),
        ],
    )

    # 21. Conclusiones
    doc.add_heading("21. Conclusiones", level=1)
    add_p(
        doc,
        "La evolución del proyecto SAJONA resolvió íntegramente las inconsistencias detectadas en los artefactos originales de 2021 y superó las limitaciones operativas de una aplicación web dependiente de red, materializando una PWA Mobile-First y Offline-First real, desplegada y verificada en producción sobre contenedores Docker con aislamiento de red y HTTPS.",
    )
    add_p(
        doc,
        "La correspondencia estricta entre el modelo de vistas 4+1 documentado, los contratos de la API REST, el motor de sincronización con idempotencia e IndexedDB y la batería de pruebas unitarias, de integración, accesibilidad y E2E respalda la madurez técnica del sistema para su validación operativa en entornos reales de cultivo medicinal (TRL-6).",
    )

    # 22. Referencias Bibliográficas
    doc.add_heading("22. Referencias Bibliográficas", level=1)
    add_bullets(
        doc,
        [
            ("Kruchten, P. (1995).", "Architectural Blueprints — The '4+1' View Model of Software Architecture. IEEE Software, 12(6), 42–50."),
            ("Fielding, R. T. (2000).", "Architectural Styles and the Design of Network-based Software Architectures. University of California, Irvine."),
            ("Kleppmann, M. (2017).", "Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems. O'Reilly Media."),
            ("World Wide Web Consortium (W3C). (2023).", "Web Content Accessibility Guidelines (WCAG) 2.2 & Service Workers Specification."),
            ("OWASP Foundation. (2021).", "Application Security Verification Standard (ASVS) v4.0.3."),
            ("Internet Engineering Task Force (IETF). (2015, 2022).", "RFC 7519 (JSON Web Token) y RFC 9110 (HTTP Semantics)."),
            ("SAJONA ADE. (2021–2026).", "Artefactos base del proyecto: Análisis de Requerimientos, Historias CV-01 a CV-09, Mockups_SAJONA.pdf, modelo_pdf_sajona.pdf, Prediseno.pptx y Plan de Calidad y Gobernanza."),
        ],
    )

    # 23. Anexos
    doc.add_heading("23. Anexos Técnicos", level=1)
    add_p(
        doc,
        "Los códigos fuente de los 12 diagramas (formato Mermaid .mmd), sus exportaciones en alta resolución monocromática (.png), el código fuente de la aplicación, las colecciones de pruebas y la guía operativa de despliegue y respaldo acompañan este documento en el repositorio de entregables.",
    )
    add_bw_table(
        doc,
        ["Ruta de Endpoint API REST v1", "Método(s)", "Propósito Arquitectónico"],
        [
            ["/health  |  /api/v1/health", "GET", "Verificación de disponibilidad del servicio y conexión PostgreSQL."],
            ["/api/v1/auth/login, /refresh, /logout, /me", "POST / GET", "Autenticación Argon2id, emisión JWT y rotación de cookie HttpOnly."],
            ["/api/v1/auth/password-reset/request y /confirm", "POST", "Flujo seguro de restablecimiento de contraseña mediante token temporal."],
            ["/api/v1/entities/{entity_type}", "GET / POST / PUT / DELETE", "Operación CRUD uniforme con RBAC, reglas de dominio y soft-delete."],
            ["/api/v1/entities/lotes/{lote_id}/trazabilidad", "GET", "Consolidado 360° de la cadena productiva e inventario vivo del lote."],
            ["/api/v1/sync/push  |  /api/v1/sync/pull", "POST / GET", "Sincronización Offline-First idempotente, detección de conflictos y pull delta."],
            ["/api/v1/admin/users, /roles, /audit-logs", "GET / POST / PATCH", "Administración RBAC y consulta de bitácora inmutable."],
        ],
        col_widths=[2.4, 1.4, 2.7],
        caption="Tabla 6. Inventario de endpoints implementados y documentados en OpenAPI.",
    )


def render_pdf_and_scan_pages() -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(OUT_DIR),
            str(DOCX_PATH),
        ],
        check=True,
    )
    toc_targets = [
        "1. Introducción",
        "2. Propósito y Alcance",
        "3. Contexto del Sistema",
        "4. Antecedentes, Auditoría e Ingeniería Inversa del Proyecto Existente",
        "5. Objetivos Arquitectónicos",
        "6. Requisitos Arquitectónicamente Significativos (ASR)",
        "7. Restricciones y Decisiones Tecnológicas",
        "8. Descripción General de la Arquitectura",
        "9. Vista Lógica",
        "9.1 Modelo Entidad-Relación Unificado",
        "9.2 Clases de Dominio e Invariantes",
        "9.3 Componentes Lógicos y Subdominios",
        "10. Vista de Procesos",
        "10.1 Flujo Agronómico Completo por Lote",
        "10.2 Sincronización Offline-First e Idempotencia",
        "10.3 Concurrencia Optimista y Resolución de Conflictos",
        "11. Vista de Desarrollo o Implementación",
        "12. Vista Física o de Despliegue",
        "13. Escenarios o Casos de Uso (+1)",
        "14. Estrategia Offline-First",
        "15. Persistencia y Sincronización",
        "16. Seguridad",
        "17. Integraciones y Comunicación entre Componentes",
        "18. Decisiones Arquitectónicas y sus Justificaciones",
        "19. Estrategia de Pruebas y Validación Arquitectónica",
        "20. Consideraciones de Rendimiento, Escalabilidad y Mantenibilidad",
        "21. Conclusiones",
        "22. Referencias Bibliográficas",
        "23. Anexos Técnicos",
    ]
    fig_targets = [
        "Figura 1. Diagrama de Contexto del Sistema SAJONA PWA",
        "Figura 2. Modelo Entidad-Relación Unificado de SAJONA (18 Tablas)",
        "Figura 3. Diagrama de Clases del Núcleo de Dominio (sajona.domain)",
        "Figura 4. Diagrama de Componentes Lógicos y Subdominios Funcionales",
        "Figura 5. Diagrama de Actividades del Ciclo Productivo Unificado por Lote",
        "Figura 6. Diagrama de Secuencia de Escritura Offline, Push Idempotente y Pull Delta",
        "Figura 7. Diagrama de Secuencia de Detección y Resolución de Conflictos Concurrentes",
        "Figura 8. Arquitectura en Capas Estricta del Backend y Reglas de Dependencia",
        "Figura 9. Diagrama de Paquetes y Módulos del Sistema (Frontend PWA y Backend)",
        "Figura 10. Diagrama de Despliegue Físico en VPS con Docker Compose y Túnel TLS 1.3",
        "Figura 11. Diagrama de Casos de Uso por Perfil RBAC del Sistema SAJONA PWA",
        "Figura 12. Escenario +1: Flujo End-to-End de Operario Sin Conectividad y Recuperación",
    ]
    tbl_targets = [
        "Tabla 1. Resumen de brechas y defectos corregidos tras la ingeniería inversa.",
        "Tabla 2. Requisitos Arquitectónicamente Significativos y métricas verificadas.",
        "Tabla 3. Especificación de contenedores desplegados en producción.",
        "Tabla 4. Registro de Decisiones Arquitectónicas (ADR-001 a ADR-005).",
        "Tabla 5. Consolidado real de validación arquitectónica y pruebas ejecutadas.",
        "Tabla 6. Inventario de endpoints implementados y documentados en OpenAPI.",
    ]

    toc_pages: dict[str, int] = {}
    fig_pages: dict[str, int] = {}
    tbl_pages: dict[str, int] = {}

    pdf_doc = pymupdf.open(str(PDF_PATH))
    # Páginas 1..3 corresponden a portada, TOC e Índice; el cuerpo inicia desde página 4 (índice 3)
    for page_idx in range(3, len(pdf_doc)):
        text = " ".join(pdf_doc[page_idx].get_text("text").split())
        page_num = page_idx + 1
        for title in toc_targets:
            if title not in toc_pages and title in text:
                toc_pages[title] = page_num
        for fig in fig_targets:
            if fig not in fig_pages and fig in text:
                fig_pages[fig] = page_num
        for tbl in tbl_targets:
            if tbl not in tbl_pages and tbl in text:
                tbl_pages[tbl] = page_num
    pdf_doc.close()
    return toc_pages, fig_pages, tbl_pages


def build_once(
    toc_pages: dict[str, int] | None = None,
    fig_pages: dict[str, int] | None = None,
    tbl_pages: dict[str, int] | None = None,
):
    doc = Document()
    configure_styles(doc)
    add_header_footer(doc)
    build_cover(doc)
    build_toc(doc, toc_pages, fig_pages, tbl_pages)
    populate_sections(doc)
    doc.save(str(DOCX_PATH))


def main():
    toc_pages: dict[str, int] | None = None
    fig_pages: dict[str, int] | None = None
    tbl_pages: dict[str, int] | None = None

    for attempt in range(1, 4):
        build_once(toc_pages, fig_pages, tbl_pages)
        new_toc, new_fig, new_tbl = render_pdf_and_scan_pages()
        if (new_toc, new_fig, new_tbl) == (toc_pages, fig_pages, tbl_pages):
            print(f"Paginación TOC e Índices convergida en pasada {attempt}.")
            break
        toc_pages, fig_pages, tbl_pages = new_toc, new_fig, new_tbl
        print(
            f"Pasada {attempt}: mapeados {len(toc_pages)}/29 títulos, {len(fig_pages)}/12 figuras, {len(tbl_pages)}/6 tablas."
        )

    print(f"DOCX generado exitosamente en: {DOCX_PATH}")
    print(f"PDF generado exitosamente en: {PDF_PATH}")


if __name__ == "__main__":
    main()
