# AGENTS.md — SAJONA PWA (Contexto Permanente de Ingeniería)

## 1. Identidad del Proyecto
- **Sistema:** SAJONA — Plataforma Web Progresiva (PWA) Mobile-First y Offline-First para el control, trazabilidad por lotes y seguimiento productivo del cultivo de cannabis medicinal.
- **Cliente / Dominio:** SAJONA ADE (NIT `900905923`).
- **Contexto Académico:** Universidad Surcolombiana (USCO) — Programa de Ingeniería de Software.
  - **Docente Supervisor y Product Owner:** Eduardo Martínez Vidal.
  - **Equipo de Trabajo (horizontal, sin jerarquías impuestas):** Danna Nerieth Palencia & Jairo Molano Salgado.

## 2. Arquitectura y Reglas de Dependencia (Monolito Modular por Capas + PWA Offline-First)
### Backend (`backend/src/sajona/`)
1. `domain/`: Entidades, Value Objects, Enums, Excepciones y Cálculos Puros. **PROHIBIDO** importar FastAPI, SQLAlchemy, Pydantic o módulos de capas superiores.
2. `application/`: Casos de uso, interfaces/puertos (`Protocol`), DTOs y lógica de sincronización (`SyncService`). Solo importa `domain/` y biblioteca estándar/Pydantic.
3. `infrastructure/`: Modelos SQLAlchemy 2, repositorios PostgreSQL, Argon2id/JWT, logger de auditoría JSON append-only, Alembic, seed inicial. Implementa puertos de `application/`.
4. `presentation/`: Routers FastAPI (`/api/v1/*`), middleware de `correlation_id`, manejador uniforme de errores RFC 7807-like, `/health`.
- Verificación obligatoria con `import-linter`, `mypy --strict` y `ruff` (complejidad ciclomática <= 10).

### Frontend PWA (`frontend/src/`)
- React 18 + TypeScript (`strict: true`) + Vite + Tailwind CSS + Dexie.js (IndexedDB) + Workbox (`sw.ts`).
- **Offline-First Real:** Toda escritura operativa pasa por el repositorio local en IndexedDB + cola `outbox_mutations` con `client_mutation_id` (UUIDv4) y `base_version`, funcionando 100% sin red y sincronizando automáticamente al recuperar conectividad (`POST /api/v1/sync/push` + `GET /api/v1/sync/pull`).
- **Seguridad Local:** Prohibido guardar contraseñas en texto plano o hashes del servidor en `localStorage` o `IndexedDB`. La sesión offline se valida mediante reclamos firmados con expiración limitada y token de actualización en cookie `HttpOnly`.

## 3. Comandos de Verificación
- Backend lint + types + architecture + tests:
  `cd backend && ruff check src tests && mypy src && lint-imports && pytest --cov=sajona --cov-report=term-missing`
- Frontend types + unit tests + build:
  `cd frontend && npx tsc --noEmit && npm test && npm run build`
- Infraestructura completa:
  `docker compose up -d --build`
