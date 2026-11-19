# ADR-001: Corrección del Modelo Entidad-Relación y Unificación de Flujo por Lote

- **Estado:** Aceptada
- **Fecha:** 2026-11-18
- **Contexto:** El modelo ER original (`modelo_pdf_sajona.pdf`) contiene errores bloqueantes de tipos (`post_cbd DECIMAL(1,2)`, `usr_password VARCHAR(20)`, `pm_fecha_esquejacion NUMERIC`, `func_numero_contacto NUMERIC`), FK invertida en `transplante` (`tp_pm_id -> planta_madre`), falta de FK explícita `usuario <-> funcionario` y ausencia de catálogos, historia clínica (`CV-07`), auditoría y metadatos de sincronización offline.
- **Decisión:**
  1. Reemplazar los PK enteros secuenciales de negocio por **UUIDv4 generados en cliente/servidor** (`id UUID PRIMARY KEY`), manteniendo un `codigo_lote` único legible en `propagaciones` para garantizar creación relacional offline sin colisiones.
  2. Corregir tipos: `password_hash VARCHAR(255)`, `porcentaje_cbd DECIMAL(5,2)`, `porcentaje_thc DECIMAL(5,2)`, fechas en `DATE` / `TIMESTAMPTZ`, `email VARCHAR(255)`, `telefono VARCHAR(30)`.
  3. Unificar el flujo alrededor de `lote_id` (`propagaciones`), haciendo que `transplantes` (tanto etapa `BOLSA` como `CAMPO`) referencien a `propagaciones(id)` (y opcionalmente a un trasplante origen), eliminando el bloqueo `tp_pm_id`.
  4. Separar `plantas_madre` (inventario de madres por lote) y `extracciones_material` (esquejes/semillas por fecha y planta madre), evitando ambigüedad en `CV-02` + `CV-09`.
  5. Añadir catálogos parametrizables (`variedades`, `ubicaciones`, `tipos_complicacion`), `controles_fase` (`CV-07`), `audit_logs`, `processed_mutations` (idempotencia de sync) y columnas transversales `version`, `updated_at`, `deleted_at`.
- **Consecuencias:** Permite integridad referencial estricta en PostgreSQL e IndexedDB y soporta el 100% de los flujos V1+V2 en modo conectado y desconectado.
