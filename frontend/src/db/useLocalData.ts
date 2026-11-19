import { useCallback, useEffect, useState } from "react";
import { db, tableForEntity } from "../db/schema";
import {
  enqueueLocalMutation,
  getSyncSnapshot,
  runSyncCycle,
  subscribeSyncUpdates,
  type SyncStatusSnapshot,
} from "../db/syncEngine";
import { generarUuid } from "../domain/calculations";
import type { BaseEntity, SyncEntityType } from "../domain/types";

export function useSyncStatus(): SyncStatusSnapshot {
  const [snapshot, setSnapshot] = useState<SyncStatusSnapshot>({
    isOnline: typeof navigator !== "undefined" ? navigator.onLine : true,
    isSyncing: false,
    pendingCount: 0,
    conflictCount: 0,
    failedCount: 0,
    lastSyncAt: null,
    lastError: null,
  });

  useEffect(() => {
    let active = true;
    const refresh = async (): Promise<void> => {
      const next = await getSyncSnapshot();
      if (active) setSnapshot(next);
    };
    void refresh();
    const unsub = subscribeSyncUpdates(() => void refresh());
    const onNet = (): void => {
      void refresh();
    };
    window.addEventListener("online", onNet);
    window.addEventListener("offline", onNet);
    return () => {
      active = false;
      unsub();
      window.removeEventListener("online", onNet);
      window.removeEventListener("offline", onNet);
    };
  }, []);

  return snapshot;
}

export function useEntityList<T extends BaseEntity>(entityType: SyncEntityType): {
  items: T[];
  loading: boolean;
  reload: () => Promise<void>;
} {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const all = (await tableForEntity(db, entityType).toArray()) as unknown as T[];
      const activeRows = all
        .filter((r) => !r.deleted_at)
        .sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? ""));
      setItems(activeRows);
    } finally {
      setLoading(false);
    }
  }, [entityType]);

  useEffect(() => {
    void reload();
    const unsub = subscribeSyncUpdates(() => void reload());
    return unsub;
  }, [reload]);

  return { items, loading, reload };
}

export async function saveEntityOfflineFirst(
  entityType: SyncEntityType,
  payload: Record<string, unknown>,
  existing?: BaseEntity | null
): Promise<string> {
  const entityId = existing ? existing.id : String(payload.id || generarUuid());
  const operation = existing ? "UPDATE" : "CREATE";
  const baseVersion = existing ? existing.version : 0;
  await enqueueLocalMutation(entityType, entityId, operation, { ...payload, id: entityId }, baseVersion);
  if (typeof navigator !== "undefined" && navigator.onLine) {
    void runSyncCycle();
  }
  return entityId;
}

export async function deleteEntityOfflineFirst(
  entityType: SyncEntityType,
  existing: BaseEntity
): Promise<void> {
  await enqueueLocalMutation(entityType, existing.id, "DELETE", {}, existing.version);
  if (typeof navigator !== "undefined" && navigator.onLine) {
    void runSyncCycle();
  }
}
