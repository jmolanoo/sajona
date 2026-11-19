/// <reference lib="webworker" />
import { clientsClaim } from "workbox-core";
import { createHandlerBoundToURL, precacheAndRoute, cleanupOutdatedCaches } from "workbox-precaching";
import { NavigationRoute, registerRoute } from "workbox-routing";
import { NetworkOnly } from "workbox-strategies";

declare let self: ServiceWorkerGlobalScope;

self.skipWaiting();
clientsClaim();
cleanupOutdatedCaches();

precacheAndRoute(self.__WB_MANIFEST);

// Todas las peticiones API se manejan por red / SyncEngine + IndexedDB sin cacheo ambiguo.
registerRoute(
  ({ url }) => url.pathname.startsWith("/api/") || url.pathname === "/health",
  new NetworkOnly()
);

// Cualquier navegación SPA en modo sin conexión sirve el App Shell precacheado.
const navHandler = createHandlerBoundToURL("/index.html");
registerRoute(
  new NavigationRoute(navHandler, {
    denylist: [/^\/api\//, /^\/health$/],
  })
);

self.addEventListener("sync", (event: Event) => {
  const syncEvent = event as ExtendableEvent & { tag?: string };
  if (syncEvent.tag === "sajona-outbox-sync") {
    syncEvent.waitUntil(
      self.clients.matchAll({ type: "window" }).then((clients) => {
        for (const client of clients) {
          client.postMessage({ type: "SAJONA_TRIGGER_SYNC" });
        }
      })
    );
  }
});
