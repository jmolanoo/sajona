# ADR-002: Evolución desde Web Online-Only (Gobernanza) hacia PWA Mobile-First y Offline-First

- **Estado:** Aceptada (Apartamiento justificado del documento `Gobernanza`)
- **Fecha:** 2026-11-18
- **Contexto:** `Gobernanza` y `SAJONA - Análisis Integral` asumían una aplicación web tradicional dependiente de conexión continua al servidor. Sin embargo, los usuarios operativos de SAJONA ADE trabajan en invernaderos, casas malla y cultivos en campo con conectividad móvil intermitente o nula.
- **Limitaciones de la disposición original:** Una web tradicional pierde los formularios diligenciados o bloquea el registro de trasplantes, revisiones, controles sanitarios, cosechas y bajas cuando cae la red móvil.
- **Decisión:** Adoptar una arquitectura **PWA Mobile-First + Offline-First**:
  - Service Worker (Workbox `injectManifest`) precacheando el App Shell completo y ofreciendo fallback de navegación offline en todas las rutas.
  - Persistencia local estructurada en **IndexedDB (Dexie.js)** con réplica de catálogos y registros activos.
  - **Outbox transaccional** (`outbox_mutations`) que registra cada escritura offline con `client_mutation_id` (UUIDv4), orden topológico causal y `base_version`.
  - Sincronización delta bidireccional (`POST /api/v1/sync/push` + `GET /api/v1/sync/pull`) con **idempotencia en servidor** (`processed_mutations`), **reintento con backoff exponencial** y **detección de conflictos por control de versiones optimista** con interfaz de resolución explícita por el usuario.
- **Beneficios:** Operación continua en campo, experiencia táctil diseñada para smartphones, cero pérdida de datos ante caídas de red o cierre de la app, y exportación de reportes (Excel, TXT, PDF) incluso sin conexión.
- **Consecuencias / Riesgos mitigados:** Mayor complejidad en la gestión de estados sincronizados y conflictos, mitigada mediante UUIDv4, pruebas unitarias dedicadas al `syncEngine` y pruebas E2E de desconexión/reconexión/concurrencia.
