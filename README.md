# SAJONA — Plataforma PWA Mobile-First y Offline-First de Trazabilidad Agrícola (TRL-6)

Sistema integral de control, seguimiento fenológico, trazabilidad por lotes y análisis químico postcosecha para el cultivo de cannabis medicinal de **SAJONA ADE (NIT 900905923)**, evolucionado a una **Aplicación Web Progresiva (PWA)** diseñada bajo principios **Mobile-First** y **Offline-First**.

## Contexto Institucional y Responsables

- **Institución:** Universidad Surcolombiana (USCO) — Programa de Ingeniería de Software
- **Docente Supervisor y Product Owner:** Ing. Eduardo Martínez Vidal
- **Equipo de Ingeniería (Co-Desarrollo Horizontal):**
  - Danna Nerieth Palencia
  - Jairo Molano Salgado
- **Cliente / Dominio de Negocio:** SAJONA ADE (NIT 900905923)

---

## Arquitectura y Capacidades Principales

- **Backend Modular en 4 Capas (`backend/`):** Python 3.12, FastAPI 0.115.6, SQLAlchemy 2.0 asíncrono, PostgreSQL 16.6, Argon2id (`pwdlib`), JWT Bearer de corta duración + Refresh Token opaco rotatorio en cookie `HttpOnly`, control de acceso RBAC (`ADMIN`, `JEFE_PROYECTO`, `OPERARIO`, `CONSULTA`) y bitácora append-only en tabla `audit_logs` + archivo JSONL (`/app/audit_logs/audit.jsonl`).
- **PWA Offline-First (`frontend/`):** React 18, TypeScript en modo estricto, Tailwind CSS, Workbox (`vite-plugin-pwa` en modo `injectManifest` -> `src/sw.ts`) y Dexie 4 sobre IndexedDB (`sajonadb`) con cola local `outbox_mutations`, orden topológico causal, idempotencia (`client_mutation_id`) y detección/resolución de conflictos lado a lado (`SyncCenterModal`).
- **Cobertura Funcional Completa (13 Vistas):** Autenticación y recuperación de contraseña, Dashboard operativo, Catálogos de Parámetros Maestros (Variedades, Ubicaciones y Tipos de Complicación), Propagación, Transplante a Bolsa, Planta Madre y Extracciones (con derivación de lotes hijos), Transplante a Campo, Plan de Control e Historia Clínica, Cosecha, Post Cosecha (`%CBD` y `%THC` en `NUMERIC(5,2)`), Bajas Transversales, Reportes con exportación local offline (`.xlsx`, `.txt`, `.pdf`) y Trazabilidad 360°, Administración RBAC y Bitácora de Auditoría.
- **Despliegue Productivo en Contenedores (`docker-compose.yml`):** 5 servicios aislados en dos redes Docker (`sajona-frontend-net` y `sajona-backend-net` con `internal: true`), proxy inverso Nginx 1.27.3 no-root (`127.0.0.1:8088`), respaldos automáticos `pg_dump` diarios con verificación y túnel cifrado TLS 1.3 vía `cloudflare/cloudflared:2026.11.1`.

---

## URL Pública Desplegada y Credenciales de Demostración

- **Aplicación PWA (HTTPS TLS 1.3):** `https://reading-store-york-writers.trycloudflare.com`
- **Healthcheck local en VPS:** `http://127.0.0.1:8088/health`

| Usuario | Correo | Rol | Contraseña Demo | Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `admin` | `admin@sajona.co` | `ADMIN` | `SajonaAdmin2026!` | Administración, RBAC, parámetros, auditoría y operación |
| `jefe` | `jefe@sajona.co` | `JEFE_PROYECTO` | `SajonaJefe2026!` | Control productivo integral, cierre y reportes |
| `operario` | `operario@sajona.co` | `OPERARIO` | `SajonaCampo2026!` | Registro en campo online/offline y sincronización |
| `consulta` | `consulta@sajona.co` | `CONSULTA` | `SajonaAudit2026!` | Lectura y exportación de reportes |

---

## Estructura del Repositorio

```text
sajona/
├── backend/                     # API REST FastAPI + arquitectura limpia en 4 capas
│   ├── src/sajona/
│   │   ├── domain/              # Entidades puras, enums, reglas agronómicas, excepciones
│   │   ├── application/         # DTOs, servicios, puertos, RBAC y motor SyncService
│   │   ├── infrastructure/      # Modelos SQLAlchemy, repositorios, Argon2id/JWT, auditoría, seed
│   │   └── presentation/        # Routers HTTP /api/v1/* y DI
│   ├── tests/                   # Pruebas unitarias e integración async con pytest + httpx
│   ├── Dockerfile               # Imagen python:3.12.7-slim no-root (UID 1001)
│   └── pyproject.toml           # Configuración ruff, mypy --strict e import-linter
├── frontend/                    # PWA React + TypeScript + Dexie IndexedDB + Workbox SW
│   ├── public/                  # manifest.webmanifest e iconos PWA (192, 512, maskable)
│   ├── src/
│   │   ├── api/                 # Cliente HTTP con mutex de refresh token
│   │   ├── auth/                # Contexto de sesión híbrida online/offline
│   │   ├── components/          # AppShell móvil/desktop, SyncCenterModal, LotTraceModal
│   │   ├── db/                  # Esquema Dexie, syncEngine.ts, hooks locales
│   │   ├── domain/              # Reglas y cálculos locales espejo del dominio
│   │   ├── pages/               # 13 vistas funcionales Mobile-First
│   │   ├── utils/               # Exportadores offline (.xlsx, .txt, .pdf) con code-splitting
│   │   └── sw.ts                # Service Worker personalizado (injectManifest)
│   └── tests/                   # Unitarias Vitest + E2E Playwright Chromium + @axe-core
├── docker/
│   ├── backup/                  # Contenedor postgres:16.6-alpine con backup.sh y restore_test.sh
│   └── proxy/                   # Nginx 1.27.3-alpine multi-stage build + cabeceras seguras
├── docs/
│   ├── 01_auditoria/            # Auditoría integral e ingeniería inversa
│   ├── adr/                     # Registros de Decisiones Arquitectónicas (ADR-001 a ADR-005)
│   ├── arquitectura_4_plus_1/   # Documento 4+1 (.docx, .pdf y script generador)
│   ├── deployment / despliegue/ # Guía de instalación, despliegue y mantenimiento
│   ├── diagrams/                # 12 diagramas Mermaid (.mmd) y exportaciones B&W (.png)
│   └── pruebas/                 # Evidencias de pruebas, capturas y métricas reales
├── docker-compose.yml
└── .env.example
```

---

## Ejecución y Verificación Rápida

### 1. Despliegue en Producción (Docker Compose)

```bash
cp .env.example .env
# Configurar POSTGRES_PASSWORD y JWT_SECRET_KEY (>= 32 caracteres aleatorios) en .env
docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1:8088/health
```

### 2. Verificación Técnica del Backend

```bash
cd backend
.venv/bin/ruff check src tests
.venv/bin/mypy src
.venv/bin/lint-imports
.venv/bin/pytest -v --cov=sajona --cov-report=term-missing
```

### 3. Verificación Técnica de la PWA y Pruebas E2E

```bash
cd frontend
npx tsc --noEmit
npm test
npm run build
E2E_BASE_URL="https://reading-store-york-writers.trycloudflare.com" npx playwright test --reporter=list
```

### 4. Copias de Seguridad y Prueba de Restauración

```bash
docker exec sajona-backup /usr/local/bin/backup.sh
docker exec sajona-backup /usr/local/bin/restore_test.sh
```
