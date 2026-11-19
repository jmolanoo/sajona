# ADR-005: Autenticación, RBAC y Seguridad de Datos en Almacenamiento Local

- **Estado:** Aceptada
- **Fecha:** 2026-11-18
- **Contexto:** Una PWA Offline-First debe permitir cerrar y reabrir la aplicación sin conexión (Escenario 4 de pruebas), pero `Seguridad (Sección 5.3)` prohíbe almacenar información sensible (contraseñas o credenciales crudas) en mecanismos locales inadecuados.
- **Decisión:**
  1. Contraseñas hasheadas exclusivamente en servidor con **Argon2id** (`argon2-cffi` / `passlib` o `pwdlib[argon2]`), jamás almacenadas en cliente.
  2. Al autenticarse en línea, el backend emite un **Access Token JWT (HS256, vida corta 15 min)** para cabeceras `Authorization: Bearer` y un **Refresh Token rotatorio en cookie `HttpOnly; SameSite=Lax; Secure`** (cuando HTTPS está activo).
  3. Para apertura offline tras cierre de la app: el cliente conserva en IndexedDB (`offline_session`) únicamente el **perfil público del usuario, sus roles/permisos, una firma HMAC/token de sesión offline de vigencia acotada (7 días)** y nunca secretos de contraseña. Al recuperar red, el cliente renueva automáticamente vía `/api/v1/auth/refresh`; si la sesión fue revocada (`401`), conserva la cola `outbox_mutations` en IndexedDB y solicita re-autenticación antes de sincronizar.
  4. El control RBAC se aplica tanto en UI como estrictamente en cada endpoint FastAPI y en la validación de mutaciones del motor de sincronización (`/api/v1/sync/push`).
- **Consecuencias:** Garantiza usabilidad offline fluida en campo sin comprometer contraseñas ni evadir controles de autorización en servidor.
