import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SajonaDatabase } from "../db/schema";
import {
  enqueueLocalMutation,
  getSyncSnapshot,
  resolveConflictMutation,
  runSyncCycle,
} from "../db/syncEngine";
import {
  calcularDiasFloracion,
  calcularRendimientoSecado,
  calcularSaldoVivoLote,
  calcularSupervivencia,
} from "../domain/calculations";
import type { Baja, Propagacion } from "../domain/types";

describe("Cálculos agronómicos de dominio en frontend", () => {
  it("calcula supervivencia, merma y alerta correctamente", () => {
    const res = calcularSupervivencia(100, 72);
    expect(res.malas).toBe(28);
    expect(res.porcentajeBuenas).toBe(72);
    expect(res.porcentajeMalas).toBe(28);
    expect(res.alertaMerma).toBe(true);
    expect(() => calcularSupervivencia(50, 55)).toThrow();
  });

  it("calcula saldo vivo de lote descontando bajas activas", () => {
    const lote = { id: "l1", cantidad_material: 100 } as Propagacion;
    const bajas = [
      { id: "b1", lote_id: "l1", cantidad: 12, deleted_at: null },
      { id: "b2", lote_id: "l1", cantidad: 5, deleted_at: "2026-11-01" },
    ] as Baja[];
    expect(calcularSaldoVivoLote(lote, bajas)).toBe(88);
    expect(calcularDiasFloracion("2026-09-01", "2026-11-01")).toBe(61);
    expect(calcularRendimientoSecado(1000, 250)).toBe(25);
  });
});

describe("Motor Offline-First IndexedDB + Outbox + Conflictos", () => {
  let testDb: SajonaDatabase;

  beforeEach(async () => {
    testDb = new SajonaDatabase(`sajona_test_${Math.random().toString(36).slice(2)}`);
    vi.stubGlobal("navigator", { onLine: false });
  });

  it("persiste creación y actualización offline en IndexedDB sin red y sincroniza al reconectar", async () => {
    await enqueueLocalMutation(
      "propagacion",
      "lot-1",
      "CREATE",
      {
        codigo_lote: "LOT-OFF-1",
        fecha_siembra: "2026-11-18",
        tipo_propagacion: "ESQUEJE",
        variedad_id: "var-1",
        tipo_incorporacion: "PROPIA",
        cantidad_material: 40,
        cantidad_plantas_madre: 0,
        observaciones: "Offline test",
        estado: "PROPAGACION",
      },
      0,
      testDb
    );

    const snapOffline = await getSyncSnapshot(testDb);
    expect(snapOffline.pendingCount).toBe(1);
    const localRow = await testDb.propagaciones.get("lot-1");
    expect(localRow?.codigo_lote).toBe("LOT-OFF-1");
    expect(localRow?._local_sync_status).toBe("pending");

    // Simular recuperación de red + respuesta del backend
    vi.stubGlobal("navigator", { onLine: true });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.includes("/sync/push")) {
          return new Response(
            JSON.stringify({
              server_time: "2026-11-18T23:00:00Z",
              results: [
                {
                  client_mutation_id: (await testDb.outbox_mutations.toArray())[0].client_mutation_id,
                  entity_type: "propagacion",
                  entity_id: "lot-1",
                  status: "applied",
                  new_version: 1,
                  server_record: { ...localRow, version: 1 },
                },
              ],
            }),
            { status: 200 }
          );
        }
        return new Response(
          JSON.stringify({ server_cursor: "2026-11-18T23:00:01Z", changes: {} }),
          { status: 200 }
        );
      })
    );

    const result = await runSyncCycle(testDb, true);
    expect(result.pushed).toBe(1);
    const snapAfter = await getSyncSnapshot(testDb);
    expect(snapAfter.pendingCount).toBe(0);
    expect((await testDb.propagaciones.get("lot-1"))?._local_sync_status).toBe("synced");
  });

  it("detecta conflicto concurrente y permite resolver conservando servidor", async () => {
    await testDb.propagaciones.put({
      id: "lot-2",
      codigo_lote: "LOT-CONFLICT",
      fecha_siembra: "2026-11-10",
      tipo_propagacion: "SEMILLA",
      variedad_id: "var-1",
      tipo_incorporacion: "COMPRADA",
      cantidad_material: 50,
      cantidad_plantas_madre: 0,
      lote_origen_id: null,
      observaciones: "Local edit",
      estado: "PROPAGACION",
      version: 1,
      created_at: "2026-11-10T00:00:00Z",
      updated_at: "2026-11-10T00:00:00Z",
      deleted_at: null,
    });

    const mut = await enqueueLocalMutation(
      "propagacion",
      "lot-2",
      "UPDATE",
      { cantidad_material: 45, observaciones: "Local edit" },
      1,
      testDb
    );

    vi.stubGlobal("navigator", { onLine: true });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.includes("/sync/push")) {
          return new Response(
            JSON.stringify({
              server_time: "2026-11-18T23:05:00Z",
              results: [
                {
                  client_mutation_id: mut.client_mutation_id,
                  entity_type: "propagacion",
                  entity_id: "lot-2",
                  status: "conflict",
                  new_version: 2,
                  message: "Conflicto v1 vs v2",
                  server_record: {
                    id: "lot-2",
                    codigo_lote: "LOT-CONFLICT",
                    fecha_siembra: "2026-11-10",
                    tipo_propagacion: "SEMILLA",
                    variedad_id: "var-1",
                    tipo_incorporacion: "COMPRADA",
                    cantidad_material: 60,
                    cantidad_plantas_madre: 0,
                    lote_origen_id: null,
                    observaciones: "Server v2",
                    estado: "PROPAGACION",
                    version: 2,
                    created_at: "2026-11-10T00:00:00Z",
                    updated_at: "2026-11-18T23:01:00Z",
                    deleted_at: null,
                  },
                },
              ],
            }),
            { status: 200 }
          );
        }
        return new Response(
          JSON.stringify({ server_cursor: "2026-11-18T23:05:01Z", changes: {} }),
          { status: 200 }
        );
      })
    );

    const res = await runSyncCycle(testDb, true);
    expect(res.conflicts).toBe(1);
    const snap = await getSyncSnapshot(testDb);
    expect(snap.conflictCount).toBe(1);

    const queued = (await testDb.outbox_mutations.toArray())[0];
    await resolveConflictMutation(queued.sequence!, "accept_server", undefined, testDb);
    const resolvedRow = await testDb.propagaciones.get("lot-2");
    expect(resolvedRow?.cantidad_material).toBe(60);
    expect(resolvedRow?._local_sync_status).toBe("synced");
  });
});
