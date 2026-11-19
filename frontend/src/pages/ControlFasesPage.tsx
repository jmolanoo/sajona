import React, { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { LotTraceModal } from "../components/LotTraceModal";
import { ResponsiveRecordsView, type ColumnDef } from "../components/ResponsiveRecordsView";
import { Field, ModalDrawer, inputCls } from "../components/UiPrimitives";
import { deleteEntityOfflineFirst, saveEntityOfflineFirst, useEntityList } from "../db/useLocalData";
import type { ControlFase, Propagacion, TipoComplicacion } from "../domain/types";

export function ControlFasesPage(): React.ReactElement {
  const { hasPermission } = useAuth();
  const { items } = useEntityList<ControlFase>("control_fase");
  const lotes = useEntityList<Propagacion>("propagacion").items;
  const complicaciones = useEntityList<TipoComplicacion>("tipo_complicacion").items;

  const loteById = new Map(lotes.map((l) => [l.id, l.codigo_lote]));
  const compById = new Map(complicaciones.map((c) => [c.id, c.nombre]));

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<ControlFase | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);

  const [loteId, setLoteId] = useState("");
  const [plantaNum, setPlantaNum] = useState("");
  const [fase, setFase] = useState("VEGETATIVA");
  const [fechaIni, setFechaIni] = useState(new Date().toISOString().slice(0, 10));
  const [fechaFin, setFechaFin] = useState("");
  const [fechaDesc, setFechaDesc] = useState("");
  const [compId, setCompId] = useState("");
  const [tratamiento, setTratamiento] = useState("");
  const [estadoRev, setEstadoRev] = useState<"BUENA" | "MALA" | "EN_TRATAMIENTO" | "DESCARTADA">("BUENA");
  const [obs, setObs] = useState("");

  const openNew = (): void => {
    setEditing(null);
    setLoteId(lotes[0]?.id ?? "");
    setPlantaNum("");
    setFase("VEGETATIVA");
    setFechaIni(new Date().toISOString().slice(0, 10));
    setFechaFin("");
    setFechaDesc("");
    setCompId("");
    setTratamiento("");
    setEstadoRev("BUENA");
    setObs("");
    setModalOpen(true);
  };

  const openEdit = (c: ControlFase): void => {
    setEditing(c);
    setLoteId(c.lote_id);
    setPlantaNum(c.numero_planta_campo);
    setFase(c.fase_cultivo);
    setFechaIni(c.fecha_inicio);
    setFechaFin(c.fecha_fin ?? "");
    setFechaDesc(c.fecha_descarte ?? "");
    setCompId(c.tipo_complicacion_id ?? "");
    setTratamiento(c.tratamiento_aplicado);
    setEstadoRev(c.estado_revision);
    setObs(c.observaciones);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    try {
      if (fechaFin && fechaFin < fechaIni) throw new Error("La fecha final no puede ser anterior al inicio.");
      await saveEntityOfflineFirst(
        "control_fase",
        {
          lote_id: loteId,
          transplante_id: null,
          numero_planta_campo: plantaNum.trim(),
          fase_cultivo: fase,
          fecha_inicio: fechaIni,
          fecha_fin: fechaFin || null,
          fecha_descarte: fechaDesc || null,
          tipo_complicacion_id: compId || null,
          tratamiento_aplicado: tratamiento.trim(),
          estado_revision: estadoRev,
          observaciones: obs.trim(),
        },
        editing
      );
      setModalOpen(false);
      setToast({ type: "success", text: "Control de fase / historia clínica guardado." });
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error al guardar." });
    }
  };

  const columns: ColumnDef<ControlFase>[] = [
    {
      key: "lote",
      header: "Id Lote",
      render: (c) => <span className="font-bold">{loteById.get(c.lote_id) ?? "—"}</span>,
      exportValue: (c) => loteById.get(c.lote_id) ?? "",
    },
    {
      key: "planta",
      header: "Planta / Unidad",
      render: (c) => c.numero_planta_campo || "Lote completo",
      exportValue: (c) => c.numero_planta_campo || "Lote",
    },
    {
      key: "fase",
      header: "Fase",
      render: (c) => c.fase_cultivo,
      exportValue: (c) => c.fase_cultivo,
    },
    {
      key: "fecha_inicio",
      header: "Inicio",
      render: (c) => c.fecha_inicio,
      exportValue: (c) => c.fecha_inicio,
    },
    {
      key: "complicacion",
      header: "Complicación",
      render: (c) => (c.tipo_complicacion_id ? compById.get(c.tipo_complicacion_id) ?? "—" : "Ninguna"),
      exportValue: (c) => (c.tipo_complicacion_id ? compById.get(c.tipo_complicacion_id) ?? "" : "Ninguna"),
    },
    {
      key: "estado",
      header: "Estado",
      render: (c) => c.estado_revision,
      exportValue: (c) => c.estado_revision,
    },
  ];

  return (
    <>
      <ResponsiveRecordsView
        title="Plan de Control e Historia Clínica"
        subtitle="Seguimiento fenológico, revisiones periódicas, complicaciones y tratamientos (CV-05 / CV-07)."
        items={items}
        columns={columns}
        dateAccessor={(c) => c.fecha_inicio}
        searchAccessor={(c) =>
          `${loteById.get(c.lote_id) ?? ""} ${c.numero_planta_campo} ${c.fase_cultivo} ${c.estado_revision}`
        }
        loteIdAccessor={(c) => c.lote_id}
        canWrite={hasPermission("production:write")}
        canDelete={hasPermission("production:delete")}
        onNew={openNew}
        onEdit={openEdit}
        onDelete={(c) => void deleteEntityOfflineFirst("control_fase", c)}
        onTraceLot={(id) => setTraceId(id)}
        toast={toast}
        onDismissToast={() => setToast(null)}
      />

      <ModalDrawer
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Editar Control Fenológico" : "Nuevo Control / Historia Clínica"}
      >
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Id Lote" htmlFor="cf-lote" required>
              <select
                id="cf-lote"
                required
                value={loteId}
                onChange={(e) => setLoteId(e.target.value)}
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
            <Field label="Número Planta Campo (opcional)" htmlFor="cf-planta">
              <input
                id="cf-planta"
                value={plantaNum}
                onChange={(e) => setPlantaNum(e.target.value)}
                placeholder="ej. PC-12"
                className={inputCls}
              />
            </Field>
            <Field label="Fase" htmlFor="cf-fase" required>
              <select
                id="cf-fase"
                value={fase}
                onChange={(e) => setFase(e.target.value)}
                className={inputCls}
              >
                <option value="ENRAIZAMIENTO">Enraizamiento</option>
                <option value="BOLSA">Bolsa</option>
                <option value="VEGETATIVA">Vegetativa</option>
                <option value="FLORACION">Floración</option>
                <option value="CAMPO">Campo</option>
              </select>
            </Field>
            <Field label="Estado Sanitario / Revisión" htmlFor="cf-rev" required>
              <select
                id="cf-rev"
                value={estadoRev}
                onChange={(e) =>
                  setEstadoRev(
                    e.target.value as "BUENA" | "MALA" | "EN_TRATAMIENTO" | "DESCARTADA"
                  )
                }
                className={inputCls}
              >
                <option value="BUENA">Buena / Sana</option>
                <option value="EN_TRATAMIENTO">En Tratamiento</option>
                <option value="MALA">Mala / Afectada</option>
                <option value="DESCARTADA">Descartada</option>
              </select>
            </Field>
            <Field label="Fecha Inicio Fase" htmlFor="cf-fini" required>
              <input
                id="cf-fini"
                type="date"
                required
                value={fechaIni}
                onChange={(e) => setFechaIni(e.target.value)}
                className={inputCls}
              />
            </Field>
            <Field label="Fecha Final Fase" htmlFor="cf-ffin">
              <input
                id="cf-ffin"
                type="date"
                value={fechaFin}
                onChange={(e) => setFechaFin(e.target.value)}
                className={inputCls}
              />
            </Field>
            <Field label="Tipo de Complicación" htmlFor="cf-comp">
              <select
                id="cf-comp"
                value={compId}
                onChange={(e) => setCompId(e.target.value)}
                className={inputCls}
              >
                <option value="">Sin complicación</option>
                {complicaciones.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Fecha Descarte" htmlFor="cf-fdesc">
              <input
                id="cf-fdesc"
                type="date"
                value={fechaDesc}
                onChange={(e) => setFechaDesc(e.target.value)}
                className={inputCls}
              />
            </Field>
          </div>
          <Field label="Tratamiento Aplicado" htmlFor="cf-trat">
            <input
              id="cf-trat"
              value={tratamiento}
              onChange={(e) => setTratamiento(e.target.value)}
              placeholder="ej. Riego preventivo / control biológico"
              className={inputCls}
            />
          </Field>
          <Field label="Observaciones" htmlFor="cf-obs">
            <textarea
              id="cf-obs"
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
