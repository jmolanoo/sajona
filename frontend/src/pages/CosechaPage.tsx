import React, { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { LotTraceModal } from "../components/LotTraceModal";
import { ResponsiveRecordsView, type ColumnDef } from "../components/ResponsiveRecordsView";
import { Field, ModalDrawer, inputCls } from "../components/UiPrimitives";
import { deleteEntityOfflineFirst, saveEntityOfflineFirst, useEntityList } from "../db/useLocalData";
import { calcularDiasFloracion } from "../domain/calculations";
import type { Cosecha, Propagacion, Transplante } from "../domain/types";

export function CosechaPage(): React.ReactElement {
  const { hasPermission } = useAuth();
  const { items } = useEntityList<Cosecha>("cosecha");
  const lotes = useEntityList<Propagacion>("propagacion").items;
  const transplantes = useEntityList<Transplante>("transplante").items;
  const loteById = new Map(lotes.map((l) => [l.id, l.codigo_lote]));

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Cosecha | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);

  const [loteId, setLoteId] = useState("");
  const [fechaSuelo, setFechaSuelo] = useState("");
  const [fechaCosecha, setFechaCosecha] = useState(new Date().toISOString().slice(0, 10));
  const [numPlantas, setNumPlantas] = useState(50);
  const [cama, setCama] = useState("");
  const [estado, setEstado] = useState<"PENDIENTE" | "EN_PROCESO" | "FINALIZADA">("FINALIZADA");
  const [pesoVerde, setPesoVerde] = useState(10000);
  const [obs, setObs] = useState("");

  const selectLote = (id: string): void => {
    setLoteId(id);
    const campo = transplantes.find((t) => t.lote_id === id && t.etapa === "CAMPO");
    if (campo) {
      setFechaSuelo(campo.fecha_transplante);
      setCama(campo.cama);
      setNumPlantas(campo.cantidad_buenas);
    }
  };

  const openNew = (): void => {
    setEditing(null);
    const first = lotes[0]?.id ?? "";
    setFechaCosecha(new Date().toISOString().slice(0, 10));
    setFechaSuelo(new Date().toISOString().slice(0, 10));
    setNumPlantas(50);
    setCama("Cama 1");
    setEstado("FINALIZADA");
    setPesoVerde(10000);
    setObs("");
    if (first) selectLote(first);
    setModalOpen(true);
  };

  const openEdit = (c: Cosecha): void => {
    setEditing(c);
    setLoteId(c.lote_id);
    setFechaSuelo(c.fecha_suelo);
    setFechaCosecha(c.fecha_cosecha);
    setNumPlantas(c.numero_plantas);
    setCama(c.cama);
    setEstado(c.estado_cosecha);
    setPesoVerde(c.peso_verde);
    setObs(c.observaciones);
    setModalOpen(true);
  };

  const diasPreview = (() => {
    try {
      return calcularDiasFloracion(fechaSuelo, fechaCosecha);
    } catch {
      return 0;
    }
  })();

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    try {
      const dias = calcularDiasFloracion(fechaSuelo, fechaCosecha);
      await saveEntityOfflineFirst(
        "cosecha",
        {
          lote_id: loteId,
          transplante_campo_id:
            transplantes.find((t) => t.lote_id === loteId && t.etapa === "CAMPO")?.id ?? null,
          fecha_suelo: fechaSuelo,
          fecha_cosecha: fechaCosecha,
          numero_plantas: Number(numPlantas),
          cama: cama.trim(),
          estado_cosecha: estado,
          dias_floracion: dias,
          peso_verde: Number(pesoVerde),
          observaciones: obs.trim(),
        },
        editing
      );
      setModalOpen(false);
      setToast({ type: "success", text: "Registro de cosecha guardado." });
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error al guardar." });
    }
  };

  const columns: ColumnDef<Cosecha>[] = [
    {
      key: "lote",
      header: "Id Lote",
      render: (c) => <span className="font-bold">{loteById.get(c.lote_id) ?? "—"}</span>,
      exportValue: (c) => loteById.get(c.lote_id) ?? "",
    },
    { key: "fecha_suelo", header: "F. Transplante", render: (c) => c.fecha_suelo, exportValue: (c) => c.fecha_suelo },
    { key: "fecha_cosecha", header: "F. Cosecha", render: (c) => c.fecha_cosecha, exportValue: (c) => c.fecha_cosecha },
    { key: "cama", header: "Cama", render: (c) => c.cama || "—", exportValue: (c) => c.cama },
    { key: "dias", header: "Floración", render: (c) => `${c.dias_floracion} d`, exportValue: (c) => c.dias_floracion },
    { key: "peso", header: "Peso Verde (g)", render: (c) => Number(c.peso_verde).toLocaleString("es-CO"), exportValue: (c) => c.peso_verde },
    { key: "estado", header: "Estado", render: (c) => c.estado_cosecha, exportValue: (c) => c.estado_cosecha },
  ];

  return (
    <>
      <ResponsiveRecordsView
        title="Cosecha"
        subtitle="Control de producción en campo, camas, días de floración y peso verde cosechado."
        items={items}
        columns={columns}
        dateAccessor={(c) => c.fecha_cosecha}
        searchAccessor={(c) => `${loteById.get(c.lote_id) ?? ""} ${c.cama} ${c.estado_cosecha}`}
        loteIdAccessor={(c) => c.lote_id}
        canWrite={hasPermission("production:write")}
        canDelete={hasPermission("production:delete")}
        onNew={openNew}
        onEdit={openEdit}
        onDelete={(c) => void deleteEntityOfflineFirst("cosecha", c)}
        onTraceLot={(id) => setTraceId(id)}
        toast={toast}
        onDismissToast={() => setToast(null)}
      />

      <ModalDrawer
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Editar Cosecha" : "Nueva Cosecha"}
      >
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Id Lote" htmlFor="cos-lote" required>
              <select
                id="cos-lote"
                required
                value={loteId}
                onChange={(e) => selectLote(e.target.value)}
                className={inputCls}
              >
                <option value="">Seleccione...</option>
                {lotes.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.codigo_lote}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Fecha Transplante a Campo" htmlFor="cos-fsuelo" required>
              <input
                id="cos-fsuelo"
                type="date"
                required
                value={fechaSuelo}
                onChange={(e) => setFechaSuelo(e.target.value)}
                className={inputCls}
              />
            </Field>
            <Field label="Fecha de Cosecha" htmlFor="cos-fcosecha" required>
              <input
                id="cos-fcosecha"
                type="date"
                required
                value={fechaCosecha}
                onChange={(e) => setFechaCosecha(e.target.value)}
                className={inputCls}
              />
            </Field>
            <Field label="N° Plantas Cosechadas" htmlFor="cos-plantas" required>
              <input
                id="cos-plantas"
                type="number"
                min={1}
                required
                value={numPlantas}
                onChange={(e) => setNumPlantas(Number(e.target.value))}
                className={inputCls}
              />
            </Field>
            <Field label="Cama" htmlFor="cos-cama">
              <input
                id="cos-cama"
                value={cama}
                onChange={(e) => setCama(e.target.value)}
                className={inputCls}
              />
            </Field>
            <Field label="Estado de Cosecha" htmlFor="cos-est" required>
              <select
                id="cos-est"
                value={estado}
                onChange={(e) =>
                  setEstado(e.target.value as "PENDIENTE" | "EN_PROCESO" | "FINALIZADA")
                }
                className={inputCls}
              >
                <option value="PENDIENTE">Pendiente</option>
                <option value="EN_PROCESO">En Proceso</option>
                <option value="FINALIZADA">Finalizada</option>
              </select>
            </Field>
            <Field label="Peso Verde Campo (g)" htmlFor="cos-peso" required>
              <input
                id="cos-peso"
                type="number"
                min={1}
                step="0.01"
                required
                value={pesoVerde}
                onChange={(e) => setPesoVerde(Number(e.target.value))}
                className={inputCls}
              />
            </Field>
            <Field label="Días de Floración (calculado)" htmlFor="cos-dias">
              <input id="cos-dias" readOnly value={`${diasPreview} días`} className={inputCls} />
            </Field>
          </div>
          <Field label="Observaciones" htmlFor="cos-obs">
            <textarea
              id="cos-obs"
              rows={2}
              value={obs}
              onChange={(e) => setObs(e.target.value)}
              className={inputCls}
            />
          </Field>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="min-h-[44px] rounded-xl border border-slate-300 px-4 text-sm font-semibold"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="min-h-[44px] rounded-xl bg-emerald-700 px-5 text-sm font-bold text-white"
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
