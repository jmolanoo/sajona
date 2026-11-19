# Guía de Instalación, Despliegue y Mantenimiento — SAJONA PWA

## 1. Requisitos del Entorno

### Servidor / VPS de Producción
- **Sistema Operativo:** Linux Ubuntu 24.04 LTS x86_64 (verificado) o equivalente con kernel compatible con Docker Engine.
- **Motor de Contenedores:** Docker Engine + Docker Compose v2 (`docker compose`).
- **Recursos Mínimos Recomendados:** 2 vCPU, 2 GiB RAM, 10 GiB de almacenamiento disponible.
- **Conectividad Saliente:** Acceso HTTPS saliente hacia Edge de Cloudflare para el servicio `sajona-tunnel` (no requiere abrir puertos adicionales en `iptables` ni modificar reglas de firewall del host).

### Entorno de Desarrollo Local (Opcional)
- Python `>= 3.12` con `venv` y `pip`.
- Node.js `>= 20.18` y `npm`.
- Navegador Chromium para pruebas E2E de Playwright y `@axe-core/playwright`.

---

## 2. Topología de Despliegue y Seguridad

El archivo [`docker-compose.yml`](../../docker-compose.yml) orquesta cinco servicios con imágenes fijas, usuarios sin privilegios de `root`, límites de CPU/RAM y aislamiento de red:

| Servicio | Imagen Base | Usuario | Redes Docker | Función Principal |
| :--- | :--- | :--- | :--- | :--- |
| `sajona-db` | `postgres:16.6-alpine` | `postgres` | `sajona-backend-net` (`internal: true`) | Base de datos transaccional PostgreSQL 16 (volumen `sajona_pgdata`). |
| `sajona-backend` | `python:3.12.7-slim` | `sajona` (`UID 1001`) | `sajona-backend-net`, `sajona-frontend-net` | API REST FastAPI con 2 workers Uvicorn y bitácora JSONL (volumen `sajona_audit_logs`). |
| `sajona-backup` | `postgres:16.6-alpine` | `postgres` | `sajona-backend-net` (`internal: true`) | Respaldos automáticos diarios cada 24h con retención de 14 copias (volumen `sajona_backups`). |
| `sajona-proxy` | `nginx:1.27.3-alpine` | `nginx` (puerto `8080`) | `sajona-frontend-net` | Compila y sirve el bundle estático PWA + Service Worker y proxea `/api/*` y `/health` al backend. Enlace loopback `127.0.0.1:8088:8080`. |
| `sajona-tunnel` | `cloudflare/cloudflared:2026.11.1` | `nonroot` | `sajona-frontend-net` | Expone `http://sajona-proxy:8080` mediante túnel cifrado HTTPS TLS 1.3 hacia Internet para contexto seguro PWA. |

---

## 3. Instalación y Despliegue Paso a Paso

### 3.1 Preparación de Variables de Entorno

1. Ubicarse en la raíz del proyecto `/home/molano/sajona`.
2. Copiar la plantilla oficial:
   ```bash
   cp .env.example .env
   ```
3. Editar `.env` asignando contraseñas y secretos criptográficos fuertes (no versionar `.env` en Git):
   - `POSTGRES_DB=sajona`
   - `POSTGRES_USER=sajona`
   - `POSTGRES_PASSWORD=<clave_aleatoria_fuerte>`
   - `DATABASE_URL=postgresql+asyncpg://sajona:<clave_aleatoria_fuerte>@sajona-db:5432/sajona`
   - `JWT_SECRET_KEY=<secreto_aleatorio_minimo_32_caracteres>`
   - `COOKIE_SECURE=true` (requiere acceso por HTTPS, garantizado vía `sajona-tunnel`).
   - `SEED_DEMO_DATA=true` en el primer arranque para poblar roles, usuarios demo, catálogos maestros y el lote demostrativo `LOT-2026-030` de forma idempotente. En entornos productivos ya inicializados puede cambiarse a `false`.

### 3.2 Construcción y Arranque de Servicios

```bash
cd /home/molano/sajona
docker compose up -d --build
```

La etapa `builder` de `docker/proxy/Dockerfile` ejecuta `npm ci --no-audit --no-fund` y `npm run build` (`tsc && vite build`), empaquetando los 14 recursos precacheados del Service Worker (`dist/sw.js`) y `manifest.webmanifest` directamente dentro de la imagen Nginx final.

### 3.3 Verificación Posterior al Despliegue

1. Verificar estado de salud de los contenedores:
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   ```
   Todos los contenedores con healthcheck (`sajona-db`, `sajona-backend`, `sajona-proxy`) deben reportar estado `healthy`.

2. Verificar disponibilidad de la API y base de datos en localhost:
   ```bash
   curl -fsS http://127.0.0.1:8088/health
   # Respuesta esperada: {"status":"healthy","database":"connected","version":"1.0.0"}
   ```

3. Consultar la URL HTTPS asignada por `sajona-tunnel` (Quick Tunnel de Cloudflare o dominio propio mediante `TUNNEL_TOKEN` en producción permanente):
   ```bash
   docker logs sajona-tunnel 2>&1 | grep -oE "https://[a-zA-Z0-9.-]+\.trycloudflare\.com" | tail -n 1
   ```

4. Validar acceso HTTPS extremo a extremo:
   ```bash
   curl -fsS https://<subdominio>.trycloudflare.com/health
   ```

> **Nota sobre DNS Permanente:** El servicio `sajona-tunnel` utiliza Quick Tunnel (`--url http://sajona-proxy:8080`) para disponer de HTTPS TLS 1.3 inmediato sin dominio DNS comprado. Si `sajona-tunnel` se reinicia tras recrear contenedores, el subdominio aleatorio de `trycloudflare.com` cambia; para un dominio fijo corporativo (`app.sajona.co`), basta sustituir el comando por `tunnel run --token <CLOUDFLARE_TUNNEL_TOKEN>`.

---

## 4. Cabeceras de Seguridad y Reglas de Caché PWA (Nginx)

El archivo [`docker/proxy/nginx.conf`](../../docker/proxy/nginx.conf) aplica controles específicos para garantizar actualización limpia del Service Worker y evitar fugas de información:

- `location = /sw.js`: emite `Cache-Control: no-cache, no-store, must-revalidate` para que el navegador siempre valide nuevas versiones del Service Worker.
- `location = /manifest.webmanifest`: tipo MIME `application/manifest+json` con `Cache-Control: no-cache`.
- `location /assets/`: caché inmutable de 1 año (`max-age=31536000, immutable`) dado que Vite genera hashes criptográficos en los nombres de chunk.
- `location /api/`: proxy directo a `http://sajona-backend:8000` preservando `X-Forwarded-Proto $http_x_forwarded_proto` para la emisión correcta de cookies `Secure` detrás del túnel HTTPS.
- Cabeceras globales obligatorias: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` y `Permissions-Policy`.

---

## 5. Instalación como PWA en Teléfonos Móviles

1. Abrir la URL HTTPS en **Google Chrome (Android)** o **Safari (iOS 16.4+)**.
2. Iniciar sesión al menos una vez con conectividad para descargar el App Shell y poblar IndexedDB (`sajonadb`).
3. En Android/Chrome, seleccionar **"Instalar aplicación"** desde el menú del navegador; en iOS/Safari, tocar **Compartir -> Agregar a pantalla de inicio**.
4. Confirmar que la aplicación abre en modo independiente (`display: standalone`) y que al activar el **Modo Avión** permanece operativa permitiendo consultas, creación/edición de lotes, registro de bajas y exportación de reportes locales.

---

## 6. Operación, Respaldos y Mantenimiento

### 6.1 Respaldos Automáticos y Manuales

El contenedor `sajona-backup` ejecuta [`backup.sh`](../../docker/backup/backup.sh) cada 86 400 segundos (24 horas), generando archivos comprimidos `sajona_YYYYMMDDTHHMMSSZ.sql.gz` con retención automática de los últimos 14 respaldos.

- Ejecutar respaldo manual inmediato:
  ```bash
  docker exec sajona-backup /usr/local/bin/backup.sh
  ```
- Verificar integridad del archivo gzip y número de tablas DDL en el último respaldo:
  ```bash
  docker exec sajona-backup /usr/local/bin/restore_test.sh
  ```

### 6.2 Restauración ante Desastres

En caso de corrupción o migración a una nueva VPS:

```bash
# Detener escrituras en el backend antes de restaurar
docker compose stop sajona-backend
# Restaurar el respaldo deseado dentro de sajona-db
docker exec -i sajona-db sh -c 'gunzip -c | psql -U sajona -d sajona' < <ruta_al_archivo_sql_gz>
docker compose start sajona-backend
```

*(Si el respaldo reside dentro del volumen `sajona_backups`, puede copiarse al host con `docker cp sajona-backup:/backups/latest.sql.gz ./latest.sql.gz` o montarse directamente).*

### 6.3 Auditoría e Inspección de Logs

- Logs operativos de aplicación y proxy:
  ```bash
  docker compose logs -f --tail=100 sajona-backend sajona-proxy
  ```
- Bitácora append-only de auditoría en formato JSON Lines:
  ```bash
  docker exec sajona-backend tail -n 50 /app/audit_logs/audit.jsonl
  ```

### 6.4 Actualización de Versión Sin Pérdida de Datos

Los volúmenes nombrados `sajona_pgdata`, `sajona_audit_logs` y `sajona_backups` son independientes del ciclo de vida de los contenedores:

```bash
cd /home/molano/sajona
docker exec sajona-backup /usr/local/bin/backup.sh
docker compose up -d --build sajona-backend sajona-proxy
```

El Service Worker detectará la actualización en el siguiente acceso con red y actualizará el App Shell sin borrar la cola local `outbox_mutations` en IndexedDB de los operarios.
