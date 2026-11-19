# ADR-004: Estrategia de Despliegue Docker, Proxy Inverso y HTTPS en la VPS

- **Estado:** Aceptada (Complemento técnico a `Gobernanza`)
- **Fecha:** 2026-11-18
- **Contexto:** En la VPS disponible (`157.137.208.37`), el tráfico entrante público está restringido a SSH (22/2222) por las reglas de red de Oracle Cloud (`iptables` / VCN), y no existe un dominio DNS propio apuntado al servidor. Sin embargo, una PWA requiere obligatoriamente **HTTPS** (contexto seguro) para registrar Service Workers y habilitar la instalación desde móviles y escritorio.
- **Decisión:**
  - Conservar el aislamiento de red exigido por `Gobernanza`: `sajona-frontend-net` y `sajona-backend-net` (base de datos `sajona-db` exclusivamente en `sajona-backend-net`; contenedores con usuarios no-root, versiones fijadas, `healthcheck` y límites de CPU/RAM).
  - Un **proxy inverso Nginx** (`sajona-proxy`) sirve los estáticos de la PWA compilada y enruta `/api/*` hacia `sajona-backend:8000` bajo un único origen (eliminando problemas de CORS y protegiendo cookies `HttpOnly`).
  - Se acopla un servicio **`cloudflared`** dentro de `sajona-frontend-net` que establece un túnel TLS 1.3 seguro hacia Cloudflare Edge apuntando a `http://sajona-proxy:8080`, exponiendo una URL **HTTPS** pública sin abrir puertos del host ni alterar reglas de firewall existentes ni afectar otros contenedores del servidor. Adicionalmente, el proxy se enlaza localmente en `127.0.0.1:8088` para verificación y auditoría local.
- **Consecuencias:** Si se reinicia el contenedor `sajona-tunnel` usando Quick Tunnel (`trycloudflare.com`), el subdominio temporal puede rotar; queda documentado el procedimiento para enlazar un Named Tunnel / dominio fijo en producción definitiva.
