# ADR-003: Stack Tecnológico y Monolito Modular por Capas

- **Estado:** Aceptada
- **Fecha:** 2026-11-18
- **Contexto:** Se requiere un stack maduro, mantenible por un equipo pequeño, compatible con la infraestructura VPS disponible (Ubuntu 24.04 x86_64, Docker Compose), que cumpla los umbrales de Gobernanza (latencia p95 <= 500 ms, tipado estricto, reglas de dependencia verificables y pruebas automáticas).
- **Decisión:**
  - **Backend:** Python 3.12 + **FastAPI** + **SQLAlchemy 2** + **Alembic** + **PostgreSQL 16**, organizado en **Monolito Modular de 4 Capas** (`domain`, `application`, `infrastructure`, `presentation`) verificado con `import-linter`, `mypy --strict`, `ruff` (complejidad <= 10) y `pytest`.
  - **Frontend PWA:** **React 18** + **TypeScript (`strict: true`)** + **Vite** + **Tailwind CSS** + **Dexie.js** (IndexedDB) + **Workbox / vite-plugin-pwa** + `xlsx` & `jspdf` para exportación local offline + **Vitest** & **Playwright**.
- **Justificación:** Evita la complejidad operativa de microservicios manteniendo desacoplamiento estricto por capas en código; FastAPI provee OpenAPI automático y excelente rendimiento; React + TypeScript + Dexie ofrecen control determinístico sobre el motor offline sin sobrecargar dispositivos móviles de recursos limitados.
