# Auditoría e Ingeniería Inversa — Proyecto SAJONA

**Cliente:** SAJONA ADE (NIT 900905923)  
**Institución Académica:** Universidad Surcolombiana (USCO) — Programa de Ingeniería de Software  
**Docente Supervisor y Product Owner:** Eduardo Martínez Vidal  
**Equipo de Ingeniería:** Danna Nerieth Palencia & Jairo Molano Salgado  
**Nivel Objetivo:** TRL-6 (Sistema validado en entorno relevante)  

---

## 1. Inventario Completo de Artefactos Auditados en Google Drive (`SAJONA/`)

Se inspeccionaron de forma íntegra (texto, XML interno, diagramas, tablas, diapositivas y renderizado visual de cada página e imagen) los 15 artefactos contenidos en la carpeta `SAJONA`:

| # | Artefacto | Tipo / Formato | Contenido y Hallazgos Clave |
|---|-----------|----------------|-----------------------------|
| 1 | `CONTEXT/ANÁLISIS DE REQUERIMIENTOS...docx` | DOCX (texto en párrafos y tabla) | Define 3 ejes de SAJONA ADE (NIT 900905923): (a) Clonación y siembra de plantas madre en TRL-6; (b) Seguimiento de planes de control y cuidado oportuno; (c) Control de cosecha/producción y analítica en tiempo real. Menciona extensibilidad a gremios agricultores de valor agregado. |
| 2 | `CONTEXT/CV-01_Ingresar_Sistema.docx` | DOCX + 3 wireframes PNG | Historia V1 (`CannabisSoft`, `www.cannabissoft.com`). Login (`Usuario`, `Contraseña`, `¿Olvidó la contraseña?`), menú jerárquico (`Siembra -> Crear Planta Madre / Crear Esqueje-Semilla / Crear Planta`, `Revisión Periódica`, `Plan de Control`, `Renovación`, `Producción`, `Informes`, `Parámetros -> Crear Lote / Crear Cama / Crear Corte`). |
| 3 | `CONTEXT/CV-02_Crear_Planta_Madre.docx` | DOCX + 1 wireframe PNG | CRUD por planta madre individual: `Planta Número *`, `Fecha Siembra *`, `Lugar de Siembra *`, `Observación`, `Guardar`, `Consultar`, tabla con `Editar` y `Eliminar`. |
| 4 | `CONTEXT/CV-03_Listar_Plantas_Madre.docx` | DOCX + 1 wireframe PNG | Filtro por rango de fechas + `Listar` / `Listar Todas`; tabla con `Número Planta Madre`, `Esqueje (Crear)`, `Total Esquejes`, `Semilla (Crear)`, `Total Semillas`, `Consultar Planta Madre`. |
| 5 | `CONTEXT/CV-04_Crear_Esquejes.docx` | DOCX + 1 wireframe PNG | Formulario de extracción: `Procedencia Planta Madre Número *`, `Tipo producto *` (`Esqueje`, `Semilla`), `Número de Producto *`, `Fase *` (`Cubículo`, `Enraizamiento`, `Bolsa`, `Campo`, `Almacenamiento`, `Siembra Semilla`), `Fecha Inicial *`, `Fecha Final`, `Observación`. |
| 6 | `CONTEXT/CV-05_Revision_Esquejes..docx` | DOCX + 2 wireframes PNG | Revisión periódica de esquejes por `Fecha Revisión *`, `Fase *`, rango de fechas, con `Contador de Malos` y `Contador de Buenos`, radio buttons `Bueno`/`Malo` por fila y modal emergente de `Observación`. |
| 7 | `CONTEXT/CV-06_Crear_Planta_Campo.docx` | DOCX + 2 wireframes PNG | Selección de plantas madre por fechas, tabla con `Tipo Siembra` (`Semilla`/`Esqueje`), `Número Tipo Siembra`, `Crear Planta`; segundo wireframe asigna `Variedad *`, `Fecha Siembra Campo *`, `Lote *`, `Cama *`, `Número de Planta` y enlace `Control Fases`. |
| 8 | `CONTEXT/CV-07_Crear_Control_Fases_Planta_Campo.docx` | DOCX + 1 wireframe PNG | Seguimiento fenológico e historia clínica en campo: `Planta Campo Número`, `Fase *` (`Vegetativa`, etc.), `Fecha Inicio Fase *`, `Fecha Final Fase`, `Fecha de descarte`, `Tipo de complicación` (`Marchitamiento`, etc.), `Observación`. |
| 9 | `CONTEXT/CV-08_propagación.docx` | DOCX sin texto + 2 wireframes PNG (V2) | Pivote a flujo por **Lote (`Lote Id`)**. Pantalla 1: `Siembra` (`Fecha Siembra`, `Cantidad`, `Lote Id`, `Tipo Propagación: Esqueje/Semilla/Ivvitro`, `Variedad`, `Tipo Incorporación: Propia/Comprada`) + `Transplante` (`Transplante`/`Finalizado`). Pantalla 2: Modal `Transplante` con `Fecha Transplante`, `Cantidad Buenas`, `Tipo Lote (P.Madre / P.Comercial)`, `Id Terreno`, `Id Surco Inicial` hasta `Id Surco Final`, y cálculo automático de `Cantidad Malas`, `Porcentaje Malas %`, `Porcentaje Buenas %`. |
| 10 | `CONTEXT/CV-09_Crear_Esquejes_Semillas_V2.docx` | DOCX sin texto + 2 wireframes PNG (V2) | Listado de lotes madre (`Lote Id`, `Fecha Siembra`, `Fecha Transplante`, `Cantidad Buenas`, `Crear Esqueje/Semilla`). Modal `Lote 30`: `Fecha Transplante`, `Fecha Esqueje`, tabla `Número Planta Madre` (`15,16,17,18`), `Cantidad Esquejes` (`30,0,7,0`), `Cantidad Semillas` (`0,20,0,40`), totales `Total Lote Esquejes: 37` y `Total Lote Semillas: 60`. |
| 11 | `CONTEXT/Mockups_SAJONA.pdf` | PDF 10 páginas | Consolida la interfaz visual SAJONA V2 en 8 módulos (`Propagación`, `Planta Madre`, `Transplante a Bolsa`, `Transplante a Campo`, `Cosecha`, `Post Cosecha`, `Bajas`, `Reportes`) + Login y Sidebar oscura + Topbar roja con breadcrumb, fecha y usuario `Admin`. Exportación Excel/TXT/PDF en listados y módulo Reportes. |
| 12 | `CONTEXT/modelo_pdf_sajona.pdf` | PDF 1 página (ER MySQL Workbench) | Define 12 tablas: `usuario`, `usuario_rol`, `rol`, `permiso_rol`, `permiso`, `funcionario`, `propagacion`, `planta_madre`, `transplante`, `cosecha`, `post_cosecha`, `baja`. Presenta errores de tipos de datos y cardinalidades críticas (ver Sección 4). |
| 13 | `CONTEXT/Prediseno.pptx` | PPTX 14 diapositivas + 12 imágenes | Reúne wireframes V1 (`CV-01..CV-07`), lista 4 módulos adicionales (`Plan de control`, `Tratamientos Periódicos (Historia clínica)`, `Producción`, `Informes`), presupuesto 2021 (`$10.800.000 COP` en 3 meses / 90 días hábiles, Flor Opita + SENA TecnoParque) y Gantt PHVA con pruebas funcionales y de concurrencia. |
| 14 | `Gobernanza ` | Google Doc (2026-11-13) | Marco de calidad y gobernanza técnica: Docker Compose con redes `frontend-net`/`backend-net`, proxy único expuesto, monolito modular de 4 capas, `/health`, volúmenes persistentes, imágenes fijas no-root, auditabilidad JSON append-only 90 días, métricas cuantitativas (p95 <= 500ms, WCAG 2.2 AA, cobertura >= 80% / >= 90% dominio, complejidad <= 10). |
| 15 | `SAJONA - Análisis Integral del Contexto y Alcance del Proyecto` | Google Doc (2026-11-13) | Consolidado histórico (2021 + 2026) que define alcance TRL-6, tabla de actores y 6 brechas críticas iniciales. |

---

## 2. Actores, Roles y Procesos de Negocio Identificados

### Actores del Dominio Operativo
1. **Administrador del Sistema (`ADMIN`):** Visible en `Mockups_SAJONA.pdf` (`Admin`). Gestiona usuarios, funcionarios, roles, permisos (`rol`, `permiso`, `permiso_rol`, `usuario_rol`), catálogos maestros y auditoría.
2. **Jefe de Proyecto (`JEFE_PROYECTO`):** Actor principal de `CV-02` a `CV-07`. Dirige la operación agronómica completa: propagación, plantas madre, extracciones, trasplantes, planes de control, cosecha, postcosecha, bajas y reportes.
3. **Operario / Funcionario de Campo (`OPERARIO`):** Técnico registrado en `funcionario` que ejecuta en invernadero, casa malla o campo el registro de revisiones, trasplantes, controles fitosanitarios, cosechas, secado y bajas.
4. **Usuario de Consulta / Gerencia (`CONSULTA`):** Consulta de trazabilidad en tiempo real y descarga de reportes productivos (Excel, Texto, PDF) sin mutar registros.

### Cadena de Valor y Procesos de Negocio
1. **Ingreso y Seguridad:** Autenticación, recuperación de contraseña, control RBAC y auditoría inmutable de escrituras.
2. **Propagación:** Registro de lotes de siembra (`propia` o `comprada`; `esqueje`, `semilla` o `in vitro`) asignando variedad, cantidad de material y plantas madre estimadas.
3. **Transplante a Bolsa y Revisión Periódica:** Paso del lote desde propagación hacia casa malla / área de planta madre, clasificando `Tipo Lote` (`Planta Madre` o `Planta Comercial`), registrando unidades buenas sobrevivientes y calculando automáticamente unidades malas, porcentaje de éxito y porcentaje de pérdida.
4. **Planta Madre y Extracción de Material:** Administración de plantas madre por lote y registro periódico de esquejes y semillas extraídos por planta madre, con acumulados por lote y trazabilidad para derivar nuevos lotes hijos.
5. **Transplante a Campo:** Paso de lotes comerciales hacia terreno definitivo, asignando ubicación/terreno, cama y rango de surcos (`surco_inicial` a `surco_final`).
6. **Plan de Control e Historia Clínica Vegetal:** Registro por lote/fase fenológica (`Enraizamiento`, `Vegetativa`, `Floración`, etc.), complicaciones fitosanitarias (`Marchitamiento`, plagas, hongos), tratamientos y descartes.
7. **Cosecha:** Registro en campo de plantas cosechadas, días de floración, cama, estado de cosecha y **peso verde campo**.
8. **Post Cosecha (Secado y Laboratorio):** Hereda automáticamente el `peso verde campo` de Cosecha; controla fechas de inicio/fin de secado, peso de flor verde, biomasa (g), peso de flor seco (g), porcentaje de **% CBD** y **% THC** y cálculo de rendimiento/merma de secado.
9. **Bajas y Descartes:** Registro transversal de mortalidad o descartes por lote y fase de cultivo, descontando del saldo vivo del lote.
10. **Reportes y Trazabilidad:** Generación filtrada por fechas e `Id Lote` con exportación en **Excel (.xlsx)**, **Texto (.txt)** y **PDF (.pdf)**.

---

## 3. Reglas de Negocio Consolidadas

- **RN-01 (Unidad Trazable por Lote):** Todo el ciclo V2 gira en torno al `Id Lote` (`codigo_lote` único + UUID interno para creación offline sin colisiones).
- **RN-02 (Conservación de Balance Vegetal):** En cualquier momento, `bajas_acumuladas <= cantidad_material` del lote; en Transplante a Bolsa, `cantidad_buenas <= cantidad_disponible` y `cantidad_malas = cantidad_disponible - cantidad_buenas`, con porcentajes que suman exactamente 100.00%.
- **RN-03 (Bifurcación por Tipo de Lote en Bolsa):** Un lote trasplantado a bolsa como `Planta Madre` habilita su gestión en el módulo Planta Madre; uno marcado como `Planta Comercial` avanza a Transplante a Campo.
- **RN-04 (Herencia Cosecha -> Post Cosecha):** Post Cosecha hereda automáticamente `fecha_cosecha`, `numero_plantas`, `cama`, `dias_floracion` y `peso_verde_campo` desde el registro de Cosecha seleccionado; `peso_flor_seco <= peso_flor_verde` y `fecha_fin_secado >= fecha_ini_secado`.
- **RN-05 (Rangos Químicos Reales):** `% CBD` y `% THC` aceptan decimales reales entre `0.00` y `100.00` (`DECIMAL(5,2)`).
- **RN-06 (Trazabilidad y Auditabilidad Inmutable):** Toda creación, actualización o eliminación lógica (soft-delete) registra actor, marca temporal, `correlation_id`, entidad, operación, estado previo/nuevo y origen (`online` vs `offline_sync`).
- **RN-07 (Operación Offline-First con Consistencia):** Las operaciones operativas en campo se persisten localmente en IndexedDB, se encolan en un Outbox idempotente (`client_mutation_id`) y validan concurrencia optimista (`version`) al sincronizar, detectando y exponiendo conflictos sin pérdida ni duplicación de datos.

---

## 4. Inconsistencias, Defectos y Brechas Detectadas en los Artefactos Originales

1. **Defectos críticos en `modelo_pdf_sajona.pdf`:**
   - `post_cbd DECIMAL(1,2)` y `post_thc DECIMAL(1,2)`: Solo permiten valores `< 1.00%`, provocando fallo SQL ante concentraciones reales (p. ej. `14.50%` CBD). -> **Corregido a `DECIMAL(5,2)`**.
   - `usr_password VARCHAR(20)`: Impide almacenar hashes seguros (Argon2id/bcrypt superan 60–100 caracteres). -> **Corregido a `VARCHAR(255)`**.
   - `pm_fecha_esquejacion NUMERIC`: Fecha tipada erróneamente como numérica. -> **Corregido a `DATE`**.
   - Relación `usuario`–`funcionario` sin columna FK explícita y campos `func_correo VARCHAR(45)` / `func_numero_contacto NUMERIC` mal dimensionados. -> **Corregido con FK explícita `usuario.funcionario_id`, `email VARCHAR(255)` y `telefono VARCHAR(30)`**.
   - `transplante.tp_pm_id -> planta_madre.pm_id`: Dependencia lógicamente invertida para lotes que van de `Propagación -> Transplante Bolsa -> Planta Madre` o `Transplante Comercial -> Campo`. -> **Corregido vinculando `transplante` directamente a `propagacion (lote_id)` y permitiendo referencia opcional a `planta_madre` / `transplante_origen`**.
   - `post_cosecha` con columna recortada (`1 more...` en Workbench, inferida como `post_estado` por consistencia con las demás tablas).
   - Ausencia de tablas catálogo (`variedad`, `ubicacion`, `tipo_complicacion`), de `control_fase` (`CV-07`), de `extraccion_esqueje_semilla` granular por planta madre (`CV-09`), de `audit_logs` (`Gobernanza`) y de metadatos de sincronización (`version`, `updated_at`, `deleted_at`, `client_mutation_id`).
2. **Inconsistencias entre Wireframes V1 (`CV-01..CV-07`), V2 (`CV-08..CV-09`) y `Mockups_SAJONA.pdf`:**
   - En `Mockups_SAJONA.pdf` pág. 7 (`3.2 Planta Madre`), la tabla del modal titula `Cantidad Planta Madre` (15, 16, 17, 18) con valores `30 + 28 = 37` (error de suma), mientras el wireframe original `CV-09` muestra correctamente `Número Planta Madre` y `30 + 7 = 37`. -> **Se conserva la semántica correcta de `CV-09` y el cálculo real exacto.**
   - En `Mockups_SAJONA.pdf` pág. 8 (`3.4 Transplante Campo`), el modal `Nuevo` copió por error el formulario de búsqueda por fechas (`Fecha de inicio`, `Fecha de fin`, `Buscar`), omitiendo los campos de terreno, cama y surcos presentes en `CV-06` y `CV-08`. -> **Se diseña el formulario completo de Transplante a Campo con lote, fecha, cantidad, terreno/ubicación, cama, surco inicial y surco final.**
   - `Mockups_SAJONA.pdf` omitió las pantallas de `Plan de Control / Historia Clínica` (`CV-07` y `Prediseno.pptx` Diap. 11), `Revisión Periódica` (`CV-05`), `Administración de Usuarios/Roles` y `Parámetros` (`CV-01`). -> **Todas se integran coherentemente en la nueva PWA.**
   - El nombre preliminar `CannabisSoft` (`www.cannabissoft.com`) en `CV-01` fue sustituido por la marca definitiva **SAJONA**.
   - La tabla de alcance en `Gobernanza` quedó con `Pendiente: ¿qué hace el software y quién lo usa?` y orientada únicamente a web tradicional Docker sin offline. -> **Se completa formalmente y se evoluciona a PWA Mobile-First / Offline-First mediante Decisiones Arquitectónicas (ADRs).**
3. **Ausencia de código fuente previo:** No existe repositorio de código anterior en la carpeta SAJONA; todos los artefactos encontrados son documentos de análisis, diseño, modelo ER y gobernanza. La nueva PWA se construye desde cero alineada con esta auditoría.

---

## 5. Clasificación de Funcionalidades

- **Existentes en especificación y conservadas (evolucionadas a PWA):** Autenticación + recuperación de contraseña, Propagación por lote, Transplante a Bolsa con cálculo de buenas/malas, Planta Madre + extracción de esquejes/semillas, Transplante a Campo, Cosecha, Post Cosecha con % CBD/% THC, Bajas, Reportes en Excel/TXT/PDF.
- **Documentadas previamente sin mockup en V2 y ahora implementadas:** Plan de Control / Historia Clínica (`CV-07`, `Prediseno`), Revisión Periódica (`CV-05`), Gestión de Usuarios/Roles/Permisos (`modelo_pdf`), Catálogos/Parámetros (`CV-01`), Auditoría inmutable (`Gobernanza`).
- **Nuevas capacidades incorporadas por evolución Mobile-First / Offline-First:** Service Worker + Web App Manifest instalable, persistencia transaccional en IndexedDB, cola Outbox idempotente, sincronización delta bidireccional, detección y UI de resolución de conflictos optimistas, indicador persistente de conectividad/pendientes, trazabilidad 360° por lote y exportación offline de Excel/TXT/PDF.
