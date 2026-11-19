# Informe de Evidencias y Resultados de Pruebas — SAJONA PWA

**Fecha de Ejecución Verificada:** 19 de noviembre de 2026  
**Entorno Desplegado Evaluado:** VPS Ubuntu 24.04 x86_64 (Docker Compose) + Proxy Nginx (`http://127.0.0.1:8088`) + Túnel HTTPS TLS 1.3 (`https://reading-store-york-writers.trycloudflare.com`)

---

## 1. Resumen Ejecutivo de Validación

| Nivel de Verificación | Herramienta(s) | Alcance Ejecutado | Resultado Real Observado |
| :--- | :--- | :--- | :--- |
| Calidad Estática y Dependencias Backend | `ruff 0.8.3`, `mypy 1.13.0`, `import-linter 2.1` | 27 archivos fuente en `src/sajona/`, 46 archivos y 144 dependencias | **0 errores**, complejidad ciclomática `<= 10`, **2 / 2 contratos de capas cumplidos (0 rotos)**. |
| Pruebas Unitarias e Integración Backend | `pytest 8.3.4` + `httpx ASGI` + `aiosqlite` | 7 unitarias de reglas puras + 6 integración/contratos/edge-cases | **13 / 13 aprobadas** en **5.66 s**. Cobertura global: **83%** (Dominio: `entities` 100%, `enums` 100%, `exceptions` 100%, `rules` 97%). |
| Tipado Estricto y Unitarias Frontend PWA | `tsc --noEmit`, `Vitest 2.1.8` + `fake-indexeddb` | Cálculos agronómicos cliente, motor IndexedDB/Outbox y conflictos | **0 errores de compilación**; **4 / 4 pruebas aprobadas** en **433 ms**. |
| Seguridad de Dependencias Runtime | `npm audit --omit=dev --audit-level=high` | Árbol de dependencias de producción PWA | **0 vulnerabilidades altas o críticas** (2 moderadas transitivas en `uuid <11.1.1` vía `exceljs`). |
| Empaquetado PWA y Service Worker | Vite + `vite-plugin-pwa` (`injectManifest`) | Generación de chunks, code splitting de exportadores y `sw.js` | Bundle principal `index-hjASP-br.js`: **376.14 kB** (**109.65 kB gzip**); `sw.js` (18K) y chunks diferidos generados. |
| Pruebas E2E en Navegador Real (HTTPS) y WCAG | `Playwright Chromium` + `@axe-core/playwright` | Flujo completo móvil (`390x844`) y escritorio (`1280x800`) contra URL HTTPS en vivo | **1 / 1 escenario integral aprobado** (**13.7 s** caso / **14.4 s** suite); **0 violaciones críticas WCAG**. |
| Rendimiento HTTP API REST | Script Python `httpx` sobre `/api/v1/entities/propagacion` | 50 peticiones consecutivas autenticadas con token JWT | **0 errores**, `p50 = 3.93 ms`, `p95 = 4.62 ms`, `max = 20.51 ms` (meta `< 500 ms`). |
| Disponibilidad y Respaldo PostgreSQL | `/health`, `backup.sh`, `restore_test.sh` | Salud en línea vía HTTPS + volcado `pg_dump` gzip + verificación DDL | `/health`: `{"status":"healthy","database":"connected"}`; respaldo `sajona_20261119T003738Z.sql.gz` con **20 sentencias `CREATE TABLE` verificadas**. |

---

## 2. Detalle de Pruebas Automatizadas Backend (`pytest`)

Comando ejecutado en `/home/molano/sajona/backend`:
```bash
.venv/bin/ruff check src tests && .venv/bin/mypy src && .venv/bin/lint-imports && .venv/bin/pytest -v --cov=sajona --cov-report=term-missing
```

### Casos Aprobados (13 / 13)
1. `test_ac01_health_y_openapi_contract` — Contrato `/health`, `/api/v1/health` y esquema OpenAPI completo.
2. `test_ac02_autenticacion_refresh_logout_y_admin_usuarios` — Login Argon2id + JWT, rotación de cookie refresh opaco de un uso, rechazo ante reuso de refresh revocado, logout y RBAC admin/consulta.
3. `test_ac03_ciclo_completo_todas_entidades_y_auditoria` — CRUD completo de variedades, ubicaciones, complicaciones, propagación, transplante a bolsa, planta madre + extracción, transplante a campo, plan de control, cosecha, post cosecha (`14.80% CBD`, `0.45% THC`), baja y trazabilidad 360° + verificación en `audit_logs`.
4. `test_ac04_offline_sync_idempotencia_conflictos_y_rechazos` — `POST /api/v1/sync/push` con reintento idempotente (`duplicate`), detección de conflicto por `base_version` (`conflict` + registro del servidor) y `GET /api/v1/sync/pull?since=`.
5. `test_ac06_flujo_asincrono_completo_y_errores` — Flujo async multi-etapa y manejo de errores controlados.
6. `test_ac05_errores_uniformes_filtros_y_edge_cases` — Contrato `{error: {code, message, correlation_id}}`, filtros y bordes.
7. `test_rn02_calcular_supervivencia_transplante_calcula_merma_y_alerta` — Cálculo de porcentaje de supervivencia y bandera `supero_umbral_baja` (`> 20%`).
8. `test_rn02_calcular_supervivencia_rechaza_buenas_mayores_a_disponible` — Validación de integridad de saldo disponible.
9. `test_rn02_calcular_supervivencia_rechaza_disponible_cero_o_negativo` — Rechazo de lotes sin saldo.
10. `test_rn02_validar_baja_contra_saldo_actualiza_y_protege_inventario` — Descuento exacto del saldo vivo al registrar bajas y bloqueo ante exceso.
11. `test_rn05_validar_porcentaje_cannabinoide_acepta_valores_reales_decimal_5_2` — Validación `0.00 <= % <= 100.00` (supera defecto original `DECIMAL(1,2)`).
12. `test_rn04_calcular_resumen_secado_y_validacion_pesos_fechas` — Cálculo de merma/rendimiento de secado y coherencia `peso_seco <= peso_verde`.
13. `test_rn04_dias_floracion_y_rango_fechas_fase` — Cálculo de días de floración y consistencia cronológica fenológica.

---

## 3. Detalle de Pruebas Unitarias Offline Frontend (`Vitest`)

Comando ejecutado en `/home/molano/sajona/frontend`:
```bash
npx tsc --noEmit && npm test
```

### Casos Aprobados (4 / 4 — 433 ms)
- `calcula supervivencia, merma y alerta correctamente`
- `calcula saldo vivo de lote descontando bajas activas`
- `persiste creación y actualización offline en IndexedDB sin red y sincroniza al reconectar`
- `detecta conflicto concurrente y permite resolver conservando servidor`

---

## 4. Detalle de Pruebas End-to-End en Producción HTTPS (`Playwright + @axe-core`)

Comando ejecutado contra el despliegue real:
```bash
E2E_BASE_URL="https://reading-store-york-writers.trycloudflare.com" npx playwright test --reporter=list
```

Escenario integral ejecutado en viewport móvil (`390x844`) y escritorio (`1280x800`):
1. Acceso inicial con red, auditoría de accesibilidad **Axe WCAG** en Login (`0` violaciones críticas) y autenticación como `jefe`.
2. Verificación de registro activo del **Service Worker** (`navigator.serviceWorker.ready`) y **Web App Manifest** (`short_name === "SAJONA"`).
3. Auditoría **Axe WCAG** sobre Dashboard (`0` violaciones críticas).
4. Simulación de pérdida total de conectividad (`context.setOffline(true)`), aparición del indicador `"Sin conexión"`, creación offline de un lote `LOT-E2E-*` en Propagación con estado `"Pendiente"`.
5. **Cierre y reapertura completa de la pestaña sin conexión a Internet**: la PWA arranca desde el Service Worker, conserva sesión offline vigente y exhibe el lote guardado en IndexedDB.
6. Recuperación de señal (`context.setOffline(false)`): sincronización automática del Outbox (`"Todo está sincronizado con el servidor"`).
7. **Conflicto concurrente real**: otro actor (`admin`) actualiza el mismo lote en PostgreSQL vía API mientras el móvil vuelve a desconectarse y edita el mismo registro en IndexedDB; al reconectar, el sistema detecta `"Conflicto"`, abre el Centro de Sincronización mostrando `"Tu cambio local"` frente a `"Versión actual del servidor"`, y tras elegir `"Conservar mis cambios"` resuelve y reintenta exitosamente.
8. Redimensionamiento a escritorio (`1280x800`) y validación del consolidado en `"Reportes y Trazabilidad"`.

---

## 5. Evidencias Visuales Capturadas en Vivo

Las capturas reales de la aplicación desplegada en `https://reading-store-york-writers.trycloudflare.com` se almacenan en [`screenshots/`](./screenshots/):

- `01_login_mobile.png` — Autenticación Mobile-First (`390x844`).
- `02_dashboard_mobile.png` — Panel Operativo SAJONA móvil con KPIs, acciones rápidas y navegación inferior fija.
- `03_propagacion_offline_mobile.png` — Modo Offline-First activo en Propagación con tarjetas táctiles y banner informativo.
- `04_sync_center_mobile.png` — Modal Centro de Sincronización Offline-First sin conectividad.
- `05_dashboard_desktop.png` — Vista adaptada a escritorio (`1280x800`) con barra lateral completa.
- `06_reportes_desktop.png` — Vista consolidada de Reportes y Trazabilidad con valores `%CBD = 14.8%` y `%THC = 0.45%`.
