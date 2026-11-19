import React, { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { LotTraceModal } from "../components/LotTraceModal";
import { ResponsiveRecordsView, type ColumnDef } from "../components/ResponsiveRecordsView";
import { Field, ModalDrawer, inputCls } from "../components/UiPrimitives";
import { deleteEntityOfflineFirst, saveEntityOfflineFirst, useEntityList } from "../db/useLocalData";
import { calcularSaldoVivoLote } from "../domain/calculations";
import type { Baja, Propagacion, TipoComplicacion } from "../domain/types";

export function BajasPage(): React.ReactElement {
  const { hasPermission } = useAuth();
  const { items } = useEntityList<Baja>("baja");
  const lotes = useEntityList<Propagacion>("propagacion").items;
  const complicaciones = useEntityList<TipoComplicacion>("tipo_complicacion").items;

  const loteById = new Map(lotes.map((l) => [l.id, l]));
  const compById = new Map(complicaciones.map((c) => [c.id, c.nombre]));

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Baja | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);

  const [loteId, setLoteId] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [cantidad, setCantidad] = useState(1);
  const [fase, setFase] = useState("PROPAGACION");
  const [compId, setCompId] = useState("");
  const [obs, setObs] = useState("");

  const selectedLote = loteById.get(loteId);
  const saldoDisponible = selectedLote
    ? calcularSaldoVivoLote(
        selectedLote,
        items.filter((b) => !editing || b.id !== editing.id)
      )
    : 0;

  const openNew = (): void => {
    setEditing(null);
    setLoteId(lotes[0]?.id ?? "");
    setFecha(new Date().toISOString().slice(0, 10));
    setCantidad(1);
    setFase("CAMPO");
    setCompId("");
    setObs("");
    setModalOpen(true);
  };

  const openEdit = (b: Baja): void => {
    setEditing(b);
    setLoteId(b.lote_id);
    setFecha(b.fecha_baja);
    setCantidad(b.cantidad);
    setFase(b.fase_cultivo);
    setCompId(b.tipo_complicacion_id ?? "");
    setObs(b.observaciones);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    try {
      if (!selectedLote) throw new Error("Seleccione un lote.");
      if (cantidad <= 0) throw new Error("La cantidad de bajas debe ser mayor a cero.");
      if (cantidad > saldoDisponible) {
        throw new Error(`La baja (${cantidad}) supera el saldo vivo disponible (${saldoDisponible}).`);
      }
      await saveEntityOfflineFirst(
        "baja",
        {
          lote_id: loteId,
          fecha_baja: fecha,
          cantidad: Number(cantidad),
          fase_cultivo: fase,
          tipo_complicacion_id: compId || null,
          observaciones: obs.trim(),
        },
        editing
      );
      setModalOpen(false);
      setToast({ type: "success", text: "Baja / descarte registrado y saldo actualizado." });
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error al guardar." });
    }
  };

  const columns: ColumnDef<Baja>[] = [
    {
      key: "lote",
      header: "Id Lote",
      render: (b) => <span className="font-bold">{loteById.get(b.lote_id)?.codigo_lote ?? "—"}</span>,
      exportValue: (b) => loteById.get(b.lote_id)?.codigo_lote ?? "",
    },
    { key: "fecha", header: "Fecha Baja", render: (b) => b.fecha_baja, exportValue: (b) => b.fecha_baja },
    { key: "fase", header: "Fase de Cultivo", render: (b) => b.fase_cultivo, exportValue: (b) => b.fase_cultivo },
    { key: "cantidad", header: "Cantidad Bajas", render: (b) => b.cantidad, exportValue: (b) => b.cantidad },
    {
      key: "motivo",
      header: "Causa",
      render: (b) => (b.tipo_complicacion_id ? compById.get(b.tipo_complicacion_id) ?? "—" : "Operativa"),
      exportValue: (b) => (b.tipo_complicacion_id ? compById.get(b.tipo_complicacion_id) ?? "" : "Operativa"),
    },
  ];

  return (
    <>
      <ResponsiveRecordsView
        title="Bajas y Descartes"
        subtitle="Registro de mortalidad y descartes por fase con control de inventario vivo."
        items={items}
        columns={columns}
        dateAccessor={(b) => b.fecha_baja}
        searchAccessor={(b) => `${loteById.get(b.lote_id)?.codigo_lote ?? ""} ${b.fase_cultivo} ${b.observaciones}`}
        loteIdAccessor={(b) => b.lote_id}
        canWrite={hasPermission("production:write")}
        canDelete={hasPermission("production:delete")}
        onNew={openNew}
        onEdit={openEdit}
        onDelete={(b) => void deleteEntityOfflineFirst("baja", b)}
        onTraceLot={(id) => setTraceId(id)}
        toast={toast}
        onDismissToast={() => setToast(null)}
      />

      <ModalDrawer
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Editar Baja" : "Registrar Baja / Descarte"}
      >
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Id Lote" htmlFor="bj-lote" required>
              <select id="bj-lote" required value={loteId} onChange={(e) => setLoteId(e.target.value)} className={inputCls}>
                <option value="">Seleccione...</option>
                {lotes.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.codigo_lote} (Saldo vivo: {calcularSaldoVivoLote(l, items)})
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Fecha de Baja" htmlFor="bj-fecha" required>
              <input id="bj-fecha" type="date" required value={fecha} onChange={(e) => setFecha(e.target.value)} className={inputCls} />
            </Field>
            <Field label="Cantidad Bajas" htmlFor="bj-cant" required hint={`Máximo disponible: ${saldoDisponible}`}>
              <input id="bj-cant" type="number" min={1} max={Math.max(saldoDisponible, 1)} required value={cantidad} onChange={(e) => setCantidad(Number(e.target.value))} className={inputCls} />
            </Field>
            <Field label="Fase de Cultivo" htmlFor="bj-fase" required>
              <select id="bj-fase" value={fase} onChange={(e) => setFase(e.target.value)} className={inputCls}>
                <option value="PROPAGACION">Siembra / Propagación</option>
                <option value="BOLSA">Transplante Bolsa (CM)</option>
                <option value="PLANTA_MADRE">Planta Madre</option>
                <option value="CAMPO">Transplante Campo</option>
                <option value="VEGETATIVA">Vegetativa</option>
                <option value="FLORACION">Floración</option>
                <option value="COSECHA">Cosecha</option>
                <option value="POST_COSECHA">Post Cosecha</option>
              </select>
            </Field>
            <Field label="Causa / Complicación" htmlFor="bj-comp">
              <select id="bj-comp" value={compId} onChange={(e) => setCompId(e.target.value)} className={inputCls}>
                <option value="">Descarte operativo / general</option>
                {complicaciones.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <Field label="Observaciones" htmlFor="bj-obs">
            <textarea id="bj-obs" rows={2} value={obs} onChange={(e) => setObs(e.target.value)} className={inputCls} />
          </Field>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setModalOpen(false)} className="min-h-[44px] rounded-xl border border-slate-300 px-4 text-sm font-semibold">
              Cancelar
            </button>
            <button type="submit" className="min-h-[44px] rounded-xl bg-emerald-700 px-5 text-sm font-bold text-white">
              Guardar
            </button>
          </div>
        </form>
      </ModalDrawer>

      <LotTraceModal loteId={traceId} onClose={() => setTraceId(null)} />
    </>
  );
}
