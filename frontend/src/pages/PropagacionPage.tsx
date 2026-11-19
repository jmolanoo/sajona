import React, { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { LotTraceModal } from "../components/LotTraceModal";
import { ResponsiveRecordsView, type ColumnDef } from "../components/ResponsiveRecordsView";
import { Field, ModalDrawer, inputCls } from "../components/UiPrimitives";
import { deleteEntityOfflineFirst, saveEntityOfflineFirst, useEntityList } from "../db/useLocalData";
import { calcularSaldoVivoLote } from "../domain/calculations";
import type { Baja, Propagacion, Variedad } from "../domain/types";

export function PropagacionPage(): React.ReactElement {
  const { hasPermission } = useAuth();
  const { items } = useEntityList<Propagacion>("propagacion");
  const { items: variedades } = useEntityList<Variedad>("variedad");
  const { items: bajas } = useEntityList<Baja>("baja");

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Propagacion | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);

  const [codigoLote, setCodigoLote] = useState("");
  const [fechaSiembra, setFechaSiembra] = useState(new Date().toISOString().slice(0, 10));
  const [tipoProp, setTipoProp] = useState<"ESQUEJE" | "SEMILLA" | "IN_VITRO">("ESQUEJE");
  const [variedadId, setVariedadId] = useState("");
  const [tipoIncorp, setTipoIncorp] = useState<"PROPIA" | "COMPRADA">("PROPIA");
  const [cantidadMat, setCantidadMat] = useState(50);
  const [cantidadMadres, setCantidadMadres] = useState(0);
  const [observaciones, setObservaciones] = useState("");

  const varById = new Map(variedades.map((v) => [v.id, v.nombre]));

  const openNew = (): void => {
    setEditing(null);
    setCodigoLote(`LOT-${new Date().getFullYear()}-${String(items.length + 31).padStart(3, "0")}`);
    setFechaSiembra(new Date().toISOString().slice(0, 10));
    setTipoProp("ESQUEJE");
    setVariedadId(variedades[0]?.id ?? "");
    setTipoIncorp("PROPIA");
    setCantidadMat(50);
    setCantidadMadres(0);
    setObservaciones("");
    setModalOpen(true);
  };

  const openEdit = (item: Propagacion): void => {
    setEditing(item);
    setCodigoLote(item.codigo_lote);
    setFechaSiembra(item.fecha_siembra);
    setTipoProp(item.tipo_propagacion);
    setVariedadId(item.variedad_id);
    setTipoIncorp(item.tipo_incorporacion);
    setCantidadMat(item.cantidad_material);
    setCantidadMadres(item.cantidad_plantas_madre);
    setObservaciones(item.observaciones);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    try {
      if (!variedadId) throw new Error("Debe seleccionar una variedad.");
      if (cantidadMat <= 0) throw new Error("La cantidad de siembra debe ser mayor a cero.");
      await saveEntityOfflineFirst(
        "propagacion",
        {
          codigo_lote: codigoLote.trim(),
          fecha_siembra: fechaSiembra,
          tipo_propagacion: tipoProp,
          variedad_id: variedadId,
          tipo_incorporacion: tipoIncorp,
          cantidad_material: Number(cantidadMat),
          cantidad_plantas_madre: Number(cantidadMadres),
          observaciones: observaciones.trim(),
          estado: editing?.estado ?? "PROPAGACION",
        },
        editing
      );
      setModalOpen(false);
      setToast({
        type: "success",
        text: navigator.onLine
          ? "Lote guardado y sincronizado."
          : "Lote guardado localmente en IndexedDB (pendiente de sincronización).",
      });
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error al guardar." });
    }
  };

  const columns: ColumnDef<Propagacion>[] = [
    {
      key: "codigo_lote",
      header: "Id Lote",
      render: (i) => <span className="font-bold text-slate-900">{i.codigo_lote}</span>,
      exportValue: (i) => i.codigo_lote,
    },
    {
      key: "fecha_siembra",
      header: "Fecha Siembra",
      render: (i) => i.fecha_siembra,
      exportValue: (i) => i.fecha_siembra,
    },
    {
      key: "variedad",
      header: "Variedad",
      render: (i) => varById.get(i.variedad_id) ?? "—",
      exportValue: (i) => varById.get(i.variedad_id) ?? "",
    },
    {
      key: "tipo_propagacion",
      header: "Propagación",
      render: (i) => i.tipo_propagacion,
      exportValue: (i) => i.tipo_propagacion,
    },
    {
      key: "tipo_incorporacion",
      header: "Incorporación",
      render: (i) => i.tipo_incorporacion,
      exportValue: (i) => i.tipo_incorporacion,
    },
    {
      key: "saldo",
      header: "Siembra / Vivo",
      render: (i) => `${i.cantidad_material} / ${calcularSaldoVivoLote(i, bajas)}`,
      exportValue: (i) => calcularSaldoVivoLote(i, bajas),
    },
  ];

  return (
    <>
      <ResponsiveRecordsView
        title="Propagación"
        subtitle="Registro de lotes iniciales de siembra (esqueje, semilla o in vitro)."
        items={items}
        columns={columns}
        dateAccessor={(i) => i.fecha_siembra}
        searchAccessor={(i) =>
          `${i.codigo_lote} ${varById.get(i.variedad_id) ?? ""} ${i.tipo_propagacion} ${i.estado}`
        }
        loteIdAccessor={(i) => i.id}
        canWrite={hasPermission("production:write")}
        canDelete={hasPermission("production:delete")}
        onNew={openNew}
        onEdit={openEdit}
        onDelete={(i) => void deleteEntityOfflineFirst("propagacion", i)}
        onTraceLot={(id) => setTraceId(id)}
        toast={toast}
        onDismissToast={() => setToast(null)}
      />

      <ModalDrawer
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? `Editar Lote ${editing.codigo_lote}` : "Nuevo Lote de Propagación"}
        subtitle="Los cambios se almacenan localmente primero para soportar operación sin señal."
      >
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Id Lote" htmlFor="prop-cod" required>
              <input
                id="prop-cod"
                required
                value={codigoLote}
                onChange={(e) => setCodigoLote(e.target.value)}
                className={inputCls}
              />
            </Field>
            <Field label="Fecha de Propagación" htmlFor="prop-fecha" required>
              <input
                id="prop-fecha"
                type="date"
                required
                value={fechaSiembra}
                onChange={(e) => setFechaSiembra(e.target.value)}
                className={inputCls}
              />
            </Field>
            <Field label="Tipo de Propagación" htmlFor="prop-tipo" required>
              <select
                id="prop-tipo"
                value={tipoProp}
                onChange={(e) => setTipoProp(e.target.value as "ESQUEJE" | "SEMILLA" | "IN_VITRO")}
                className={inputCls}
              >
                <option value="ESQUEJE">Esqueje</option>
                <option value="SEMILLA">Semilla</option>
                <option value="IN_VITRO">In vitro</option>
              </select>
            </Field>
            <Field label="Variedad" htmlFor="prop-var" required>
              <select
                id="prop-var"
                required
                value={variedadId}
                onChange={(e) => setVariedadId(e.target.value)}
                className={inputCls}
              >
                <option value="">Seleccione...</option>
                {variedades.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.nombre} ({v.perfil})
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Tipo Incorporación" htmlFor="prop-inc" required>
              <select
                id="prop-inc"
                value={tipoIncorp}
                onChange={(e) => setTipoIncorp(e.target.value as "PROPIA" | "COMPRADA")}
                className={inputCls}
              >
                <option value="PROPIA">Propia</option>
                <option value="COMPRADA">Comprada</option>
              </select>
            </Field>
            <Field label="Cantidad de Siembra" htmlFor="prop-cant" required>
              <input
                id="prop-cant"
                type="number"
                min={1}
                required
                value={cantidadMat}
                onChange={(e) => setCantidadMat(Number(e.target.value))}
                className={inputCls}
              />
            </Field>
            <Field label="Cantidad Plantas Madre (estimado)" htmlFor="prop-madres">
              <input
                id="prop-madres"
                type="number"
                min={0}
                value={cantidadMadres}
                onChange={(e) => setCantidadMadres(Number(e.target.value))}
                className={inputCls}
              />
            </Field>
          </div>
          <Field label="Observaciones" htmlFor="prop-obs">
            <textarea
              id="prop-obs"
              rows={2}
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              className={inputCls}
            />
          </Field>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="min-h-[44px] rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="min-h-[44px] rounded-xl bg-emerald-700 px-5 text-sm font-bold text-white hover:bg-emerald-800"
            >
              Guardar
            </button>
          </div>
        </form>
      </ModalDrawer>

      <LotTraceModal loteId={traceId} onClose={() => setTraceId(null)} />
    </>
  );
}
