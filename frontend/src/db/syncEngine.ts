import { apiFetch } from "../api/client";
import { generarUuid } from "../domain/calculations";
import type { OutboxMutation, SyncEntityType } from "../domain/types";
import { db, tableForEntity, type SajonaDatabase } from "./schema";

export const ENTITY_SYNC_ORDER: SyncEntityType[] = [
  "variedad",
  "ubicacion",
  "tipo_complicacion",
  "propagacion",
  "transplante",
  "planta_madre",
  "extraccion_material",
  "control_fase",
  "cosecha",
  "post_cosecha",
  "baja",
];

export interface SyncStatusSnapshot {
  isOnline: boolean;
  isSyncing: boolean;
  pendingCount: number;
  conflictCount: number;
  failedCount: number;
  lastSyncAt: string | null;
  lastError: string | null;
}

interface SyncPushResultItem {
  client_mutation_id: string;
  entity_type: SyncEntityType;
  entity_id: string;
  status: "applied" | "duplicate" | "conflict" | "rejected";
  new_version?: number;
  server_record?: Record<string, unknown> | null;
  error_code?: string | null;
  message?: string | null;
}

interface SyncPullResponse {
  server_cursor: string;
  changes: Record<string, Array<Record<string, unknown>>>;
}

let syncInProgress = false;
const listeners = new Set<() => void>();
let lastSyncError: string | null = null;

export function subscribeSyncUpdates(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function notifySyncListeners(): void {
  for (const listener of listeners) {
    listener();
  }
}

export async function getSyncSnapshot(database: SajonaDatabase = db): Promise<SyncStatusSnapshot> {
  const all = await database.outbox_mutations.toArray();
  const meta = await database.sync_meta.get("main");
  return {
    isOnline: typeof navigator !== "undefined" ? navigator.onLine : true,
    isSyncing: syncInProgress,
    pendingCount: all.filter((m) => m.status === "queued" || m.status === "syncing").length,
    conflictCount: all.filter((m) => m.status === "conflict").length,
    failedCount: all.filter((m) => m.status === "failed").length,
    lastSyncAt: meta?.last_sync_at ?? null,
    lastError: lastSyncError,
  };
}

export async function enqueueLocalMutation(
  entityType: SyncEntityType,
  entityId: string,
  operation: "CREATE" | "UPDATE" | "DELETE",
  payload: Record<string, unknown>,
  baseVersion: number,
  database: SajonaDatabase = db
): Promise<OutboxMutation> {
  const nowIso = new Date().toISOString();
  const table = tableForEntity(database, entityType);
  const mutation: OutboxMutation = {
    client_mutation_id: generarUuid(),
    entity_type: entityType,
    entity_id: entityId,
    operation,
    base_version: baseVersion,
    payload,
    status: "queued",
    attempts: 0,
    next_retry_at: 0,
    last_error: null,
    server_record: null,
    created_at: nowIso,
  };

  await database.transaction("rw", table, database.outbox_mutations, async () => {
    const existing = await table.get(entityId);
    if (operation === "DELETE") {
      if (existing) {
        await table.put({
          ...existing,
          deleted_at: nowIso,
          updated_at: nowIso,
          _local_sync_status: "pending",
        });
      }
    } else {
      await table.put({
        ...(existing ?? {}),
        ...payload,
        id: entityId,
        version: existing ? Number(existing.version ?? baseVersion) : 1,
        created_at: existing?.created_at ?? nowIso,
        updated_at: nowIso,
        deleted_at: null,
        _local_sync_status: "pending",
      });
    }
    await database.outbox_mutations.add(mutation);
  });

  notifySyncListeners();
  void requestBackgroundSync();
  return mutation;
}

async function requestBackgroundSync(): Promise<void> {
  if (typeof navigator !== "undefined" && "serviceWorker" in navigator) {
    try {
      const reg = await navigator.serviceWorker.ready;
      const syncReg = reg as ServiceWorkerRegistration & {
        sync?: { register: (tag: string) => Promise<void> };
      };
      if (syncReg.sync) {
        await syncReg.sync.register("sajona-outbox-sync");
      }
    } catch {
      // Fallback automático gestionado por evento online y reintento en app
    }
  }
}

function sortMutationsTopologically(items: OutboxMutation[]): OutboxMutation[] {
  const rank = new Map(ENTITY_SYNC_ORDER.map((e, idx) => [e, idx]));
  return [...items].sort((a, b) => {
    const diff = (rank.get(a.entity_type) ?? 99) - (rank.get(b.entity_type) ?? 99);
    if (diff !== 0) return diff;
    return (a.sequence ?? 0) - (b.sequence ?? 0);
  });
}

async function getOrCreateDeviceId(database: SajonaDatabase): Promise<string> {
  const meta = await database.sync_meta.get("main");
  if (meta?.client_device_id) return meta.client_device_id;
  const created = {
    key: "main",
    last_pull_cursor: null,
    last_sync_at: null,
    client_device_id: generarUuid(),
  };
  await database.sync_meta.put(created);
  return created.client_device_id;
}

export async function runSyncCycle(
  database: SajonaDatabase = db,
  forceRetryAll = false
): Promise<{ pushed: number; conflicts: number; pulled: number }> {
  if (syncInProgress) return { pushed: 0, conflicts: 0, pulled: 0 };
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    return { pushed: 0, conflicts: 0, pulled: 0 };
  }

  syncInProgress = true;
  lastSyncError = null;
  notifySyncListeners();

  try {
    const now = Date.now();
    const candidates = await database.outbox_mutations
      .where("status")
      .anyOf(["queued", "syncing"])
      .toArray();
    const ready = sortMutationsTopologically(
      candidates.filter((m) => forceRetryAll || m.next_retry_at <= now)
    );

    let pushed = 0;
    let conflicts = 0;

    if (ready.length > 0) {
      const deviceId = await getOrCreateDeviceId(database);
      for (const m of ready) {
        if (m.sequence !== undefined) {
          await database.outbox_mutations.update(m.sequence, { status: "syncing" });
        }
      }

      try {
        const pushRes = await apiFetch<{ results: SyncPushResultItem[] }>("/api/v1/sync/push", {
          method: "POST",
          body: JSON.stringify({
            client_device_id: deviceId,
            mutations: ready.map((m) => ({
              client_mutation_id: m.client_mutation_id,
              entity_type: m.entity_type,
              entity_id: m.entity_id,
              operation: m.operation,
              base_version: m.base_version,
              payload: m.payload,
            })),
          }),
        });

        const byId = new Map(ready.map((m) => [m.client_mutation_id, m]));
        for (const outcome of pushRes.results) {
          const item = byId.get(outcome.client_mutation_id);
          if (!item || item.sequence === undefined) continue;
          const table = tableForEntity(database, outcome.entity_type);

          if (outcome.status === "applied" || outcome.status === "duplicate") {
            pushed += 1;
            await database.transaction("rw", table, database.outbox_mutations, async () => {
              if (outcome.server_record) {
                await table.put({ ...outcome.server_record, _local_sync_status: "synced" });
              }
              await database.outbox_mutations.delete(item.sequence!);
            });
          } else if (outcome.status === "conflict") {
            conflicts += 1;
            await database.transaction("rw", table, database.outbox_mutations, async () => {
              const currentLocal = await table.get(outcome.entity_id);
              if (currentLocal) {
                await table.put({ ...currentLocal, _local_sync_status: "conflict" });
              }
              await database.outbox_mutations.update(item.sequence!, {
                status: "conflict",
                last_error: outcome.message ?? "Conflicto de concurrencia",
                server_record: outcome.server_record ?? null,
              });
            });
          } else {
            await database.outbox_mutations.update(item.sequence, {
              status: "failed",
              last_error: outcome.message ?? "Rechazado por validación en servidor",
            });
          }
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Error de red durante sincronización";
        lastSyncError = msg;
        for (const item of ready) {
          if (item.sequence === undefined) continue;
          const nextAttempt = item.attempts + 1;
          const backoffMs = Math.min(60000, Math.pow(2, nextAttempt) * 1500);
          await database.outbox_mutations.update(item.sequence, {
            status: "queued",
            attempts: nextAttempt,
            next_retry_at: Date.now() + backoffMs,
            last_error: msg,
          });
        }
        return { pushed, conflicts, pulled: 0 };
      }
    }

    // Pull incremental
    const meta = await database.sync_meta.get("main");
    const sinceQuery = meta?.last_pull_cursor
      ? `?since=${encodeURIComponent(meta.last_pull_cursor)}`
      : "";
    const pullRes = await apiFetch<SyncPullResponse>(`/api/v1/sync/pull${sinceQuery}`);

    const lockedRows = new Set(
      (await database.outbox_mutations.toArray())
        .filter((m) => m.status === "queued" || m.status === "conflict" || m.status === "syncing")
        .map((m) => `${m.entity_type}:${m.entity_id}`)
    );

    let pulled = 0;
    for (const entityType of ENTITY_SYNC_ORDER) {
      const incoming = pullRes.changes[entityType] ?? [];
      if (incoming.length === 0) continue;
      const table = tableForEntity(database, entityType);
      for (const rec of incoming) {
        const key = `${entityType}:${String(rec.id)}`;
        if (lockedRows.has(key)) continue;
        await table.put({ ...rec, _local_sync_status: "synced" });
        pulled += 1;
      }
    }

    await database.sync_meta.put({
      key: "main",
      last_pull_cursor: pullRes.server_cursor,
      last_sync_at: new Date().toISOString(),
      client_device_id: meta?.client_device_id ?? (await getOrCreateDeviceId(database)),
    });

    return { pushed, conflicts, pulled };
  } catch (err) {
    lastSyncError = err instanceof Error ? err.message : "Error al sincronizar";
    return { pushed: 0, conflicts: 0, pulled: 0 };
  } finally {
    syncInProgress = false;
    notifySyncListeners();
  }
}

export async function resolveConflictMutation(
  sequence: number,
  resolution: "accept_server" | "keep_local" | "merge",
  mergedPayload?: Record<string, unknown>,
  database: SajonaDatabase = db
): Promise<void> {
  const mut = await database.outbox_mutations.get(sequence);
  if (!mut) return;
  const table = tableForEntity(database, mut.entity_type);

  if (resolution === "accept_server") {
    await database.transaction("rw", table, database.outbox_mutations, async () => {
      if (mut.server_record) {
        await table.put({ ...mut.server_record, _local_sync_status: "synced" });
      }
      await database.outbox_mutations.delete(sequence);
    });
    notifySyncListeners();
    return;
  }

  const serverVersion = Number(mut.server_record?.version ?? mut.base_version + 1);
  const newPayload = resolution === "merge" && mergedPayload ? mergedPayload : mut.payload;
  const nowIso = new Date().toISOString();

  await database.transaction("rw", table, database.outbox_mutations, async () => {
    const existing = await table.get(mut.entity_id);
    if (existing) {
      await table.put({
        ...existing,
        ...newPayload,
        version: serverVersion,
        updated_at: nowIso,
        _local_sync_status: "pending",
      });
    }
    await database.outbox_mutations.update(sequence, {
      client_mutation_id: generarUuid(),
      base_version: serverVersion,
      payload: newPayload,
      status: "queued",
      attempts: 0,
      next_retry_at: 0,
      last_error: null,
    });
  });

  notifySyncListeners();
  await runSyncCycle(database, true);
}

export async function retryFailedMutation(
  sequence: number,
  database: SajonaDatabase = db
): Promise<void> {
  await database.outbox_mutations.update(sequence, {
    status: "queued",
    attempts: 0,
    next_retry_at: 0,
    last_error: null,
  });
  notifySyncListeners();
  await runSyncCycle(database, true);
}

export async function discardOutboxMutation(
  sequence: number,
  database: SajonaDatabase = db
): Promise<void> {
  const mut = await database.outbox_mutations.get(sequence);
  if (!mut) return;
  const table = tableForEntity(database, mut.entity_type);
  await database.transaction("rw", table, database.outbox_mutations, async () => {
    if (mut.operation === "CREATE") {
      await table.delete(mut.entity_id);
    } else if (mut.server_record) {
      await table.put({ ...mut.server_record, _local_sync_status: "synced" });
    }
    await database.outbox_mutations.delete(sequence);
  });
  notifySyncListeners();
}
