import React, { useEffect, useState } from "react";
import { RefreshCw, AlertTriangle, CheckCircle2, Trash2, CloudOff } from "lucide-react";
import { db } from "../db/schema";
import {
  discardOutboxMutation,
  resolveConflictMutation,
  retryFailedMutation,
  runSyncCycle,
  subscribeSyncUpdates,
} from "../db/syncEngine";
import { useSyncStatus } from "../db/useLocalData";
import type { OutboxMutation } from "../domain/types";
import { ModalDrawer } from "./UiPrimitives";

export function SyncCenterModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}): React.ReactElement | null {
  const status = useSyncStatus();
  const [mutations, setMutations] = useState<OutboxMutation[]>([]);
  const [busy, setBusy] = useState(false);

  const loadQueue = async (): Promise<void> => {
    const items = await db.outbox_mutations.toArray();
    setMutations(items);
  };

  useEffect(() => {
    if (!open) return;
    void loadQueue();
    return subscribeSyncUpdates(() => void loadQueue());
  }, [open]);

  const handleManualSync = async (): Promise<void> => {
    setBusy(true);
    try {
      await runSyncCycle(db, true);
      await loadQueue();
    } finally {
      setBusy(false);
    }
  };

  return (
    <ModalDrawer
      open={open}
      onClose={onClose}
      title="Centro de Sincronización Offline-First"
      subtitle="Estado de la cola local (IndexedDB), reintentos y resolución de conflictos."
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-600">Conectividad</p>
            <p className="text-sm font-bold text-slate-900 mt-0.5">
              {status.isOnline ? "En línea" : "Sin conexión"}
            </p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-amber-50 p-3">
            <p className="text-xs text-amber-800">Pendientes</p>
            <p className="text-lg font-bold text-amber-900">{status.pendingCount}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-red-50 p-3">
            <p className="text-xs text-red-800">Conflictos</p>
            <p className="text-lg font-bold text-red-900">{status.conflictCount}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-600">Última Sync</p>
            <p className="text-xs font-semibold text-slate-900 mt-1">
              {status.lastSyncAt ? new Date(status.lastSyncAt).toLocaleString("es-CO") : "Pendiente"}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2">
          <button
            type="button"
            disabled={!status.isOnline || busy || status.isSyncing}
            onClick={() => void handleManualSync()}
            className="inline-flex min-h-[44px] items-center gap-2 rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${busy || status.isSyncing ? "animate-spin" : ""}`} />
            <span>{status.isOnline ? "Sincronizar ahora" : "Esperando conexión..."}</span>
          </button>
          {!status.isOnline && (
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-800">
              <CloudOff className="h-4 w-4" />
              Los cambios se guardan localmente de forma segura.
            </span>
          )}
        </div>

        {status.lastError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-900">
            Último aviso de red: {status.lastError}
          </div>
        )}

        {mutations.length === 0 ? (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-6 text-center">
            <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-700" />
            <p className="mt-2 text-sm font-semibold text-emerald-900">
              Todo está sincronizado con el servidor
            </p>
            <p className="text-xs text-emerald-800 mt-1">
              No existen mutaciones pendientes en la cola local.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {mutations.map((m) => (
              <div
                key={m.client_mutation_id}
                className={`rounded-xl border p-3.5 ${
                  m.status === "conflict"
                    ? "border-red-300 bg-red-50/70"
                    : m.status === "failed"
                      ? "border-orange-300 bg-orange-50/70"
                      : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wide text-slate-700">
                      {m.operation} • {m.entity_type}
                    </span>
                    <p className="text-xs text-slate-600">
                      ID: {m.entity_id.slice(0, 8)}... • Base v{m.base_version} • Estado:{" "}
                      <strong>{m.status}</strong>
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {m.status === "failed" && m.sequence !== undefined && (
                      <button
                        type="button"
                        onClick={() => void retryFailedMutation(m.sequence!)}
                        className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-semibold text-white"
                      >
                        Reintentar
                      </button>
                    )}
                    {m.sequence !== undefined && (
                      <button
                        type="button"
                        onClick={() => void discardOutboxMutation(m.sequence!)}
                        className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                        title="Descartar cambio local"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Descartar
                      </button>
                    )}
                  </div>
                </div>

                {m.last_error && (
                  <p className="mt-2 flex items-center gap-1.5 text-xs font-medium text-red-800">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    {m.last_error}
                  </p>
                )}

                {m.status === "conflict" && m.sequence !== undefined && (
                  <div className="mt-3 space-y-2 border-t border-red-200 pt-3">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      <div className="rounded-lg bg-white p-2.5 border border-slate-200">
                        <p className="font-bold text-slate-800 mb-1">Tu cambio local</p>
                        <pre className="whitespace-pre-wrap break-all text-[11px] text-slate-700">
                          {JSON.stringify(m.payload, null, 2)}
                        </pre>
                      </div>
                      <div className="rounded-lg bg-white p-2.5 border border-slate-200">
                        <p className="font-bold text-slate-800 mb-1">
                          Versión actual del servidor (v{String(m.server_record?.version ?? "?")})
                        </p>
                        <pre className="whitespace-pre-wrap break-all text-[11px] text-slate-700">
                          {JSON.stringify(m.server_record ?? {}, null, 2)}
                        </pre>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => void resolveConflictMutation(m.sequence!, "keep_local")}
                        className="min-h-[40px] rounded-lg bg-red-800 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-900"
                      >
                        Conservar mis cambios
                      </button>
                      <button
                        type="button"
                        onClick={() => void resolveConflictMutation(m.sequence!, "accept_server")}
                        className="min-h-[40px] rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-100"
                      >
                        Aceptar versión del servidor
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </ModalDrawer>
  );
}
