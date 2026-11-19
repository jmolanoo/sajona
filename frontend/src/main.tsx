import React from "react";
import ReactDOM from "react-dom/client";
import { registerSW } from "virtual:pwa-register";
import App from "./App";
import { runSyncCycle } from "./db/syncEngine";
import "./index.css";

registerSW({
  immediate: true,
});

if (typeof navigator !== "undefined" && "serviceWorker" in navigator) {
  navigator.serviceWorker.addEventListener("message", (event: MessageEvent) => {
    if (event.data && event.data.type === "SAJONA_TRIGGER_SYNC") {
      void runSyncCycle();
    }
  });
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
