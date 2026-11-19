import React, { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { LotTraceModal } from "../components/LotTraceModal";
import { ResponsiveRecordsView, type ColumnDef } from "../components/ResponsiveRecordsView";
import { Field, ModalDrawer, inputCls } from "../components/UiPrimitives";
import { deleteEntityOfflineFirst, saveEntityOfflineFirst, useEntityList } from "../db/useLocalData";
import { calcularRendimientoSecado } from "../domain/calculations";
import type { Cosecha, PostCosecha, Propagacion } from "../domain/types";

export function PostCosechaPage(): React.ReactElement {
  const { hasPermission } = useAuth();
  const { items } = useEntityList<PostCosecha>("post_cosecha");
  const cosechas = useEntityList<Cosecha>("cosecha").items;
  const lotes = useEntityList<Propagacion>("propagacion").items;

  const loteById = new Map(lotes.map((l) => [l.id, l.codigo_lote]));
  const cosechaById = new Map(cosechas.map((c) => [c.id, c]));

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<PostCosecha | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);

  const [cosechaId, setCosechaId] = useState("");
  const [fIni, setFIni] = useState(new Date().toISOString().slice(0, 10));
  const [fFin, setFFin] = useState("");
  const [pesoFlorVerde, setPesoFlorVerde] = useState(10000);
  const [pesoBiomasa, setPesoBiomasa] = useState(1500);
  const [pesoFlorSeco, setPesoFlorSeco] = useState(2500);
  const [cbd, setCbd] = useState(14.5);
  const [thc, setThc] = useState(0.45);
  const [obs, setObs] = useState("");

  const selectedCos = cosechaById.get(cosechaId);

  const selectCosecha = (id: string): void => {
    setCosechaId(id);
    const c = cosechaById.get(id);
    if (c) {
      setPesoFlorVerde(Number(c.peso_verde));
    }
  };

  const openNew = (): void => {
    setEditing(null);
    const first = cosechas[0];
    setFIni(new Date().toISOString().slice(0, 10));
    setFFin("");
    setPesoBiomasa(1500);
    setPesoFlorSeco(2500);
    setCbd(14.5);
    setThc(0.45);
    setObs("");
    if (first) selectCosecha(first.id);
    else setCosechaId("");
    setModalOpen(true);
  };

  const openEdit = (p: PostCosecha): void => {
    setEditing(p);
    setCosechaId(p.cosecha_id);
    setFIni(p.fecha_ini_secado);
    setFFin(p.fecha_fin_secado ?? "");
    setPesoFlorVerde(p.peso_flor_verde);
    setPesoBiomasa(p.peso_biomasa);
    setPesoFlorSeco(p.peso_flor_seco);
    setCbd(p.porcentaje_cbd);
    setThc(p.porcentaje_thc);
    setObs(p.observaciones);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    try {
      if (!selectedCos) throw new Error("Debe seleccionar un registro de cosecha.");
      if (pesoFlorSeco > pesoFlorVerde) {
        throw new Error("El peso de flor seca no puede superar el peso de flor verde.");
      }
      if (fFin && fFin < fIni) {
        throw new Error("La fecha fin de secado no puede ser anterior al inicio.");
      }
      if (cbd < 0 || cbd > 100 || thc < 0 || thc > 100) {
        throw new Error("Los porcentajes % CBD y % THC deben estar entre 0.00 y 100.00.");
      }
      await saveEntityOfflineFirst(
        "post_cosecha",
        {
          cosecha_id: selectedCos.id,
          lote_id: selectedCos.lote_id,
          fecha_ini_secado: fIni,
          fecha_fin_secado: fFin || null,
          peso_flor_verde: Number(pesoFlorVerde),
          peso_biomasa: Number(pesoBiomasa),
          peso_flor_seco: Number(pesoFlorSeco),
          porcentaje_cbd: Number(cbd),
          porcentaje_thc: Number(thc),
          observaciones: obs.trim(),
        },
        editing
      );
      setModalOpen(false);
      setToast({ type: "success", text: "Post cosecha y análisis químico guardados." });
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error al guardar." });
    }
  };

  const columns: ColumnDef<PostCosecha>[] = [
    {
      key: "lote",
      header: "Id Lote",
      render: (p) => <span className="font-bold">{loteById.get(p.lote_id) ?? "—"}</span>,
      exportValue: (p) => loteById.get(p.lote_id) ?? "",
    },
    { key: "fini", header: "F.I Secado", render: (p) => p.fecha_ini_secado, exportValue: (p) => p.fecha_ini_secado },
    { key: "ffin", header: "F.F Secado", render: (p) => p.fecha_fin_secado || "En curso", exportValue: (p) => p.fecha_fin_secado ?? "" },
    { key: "seco", header: "Flor Seca (g)", render: (p) => Number(p.peso_flor_seco).toLocaleString("es-CO"), exportValue: (p) => p.peso_flor_seco },
    { key: "rend", header: "Rendimiento", render: (p) => `${calcularRendimientoSecado(p.peso_flor_verde, p.peso_flor_seco)}%`, exportValue: (p) => `${calcularRendimientoSecado(p.peso_flor_verde, p.peso_flor_seco)}%` },
    { key: "cbd", header: "% CBD", render: (p) => `${p.porcentaje_cbd}%`, exportValue: (p) => p.porcentaje_cbd },
    { key: "thc", header: "% THC", render: (p) => `${p.porcentaje_thc}%`, exportValue: (p) => p.porcentaje_thc },
  ];

  return (
    <>
      <ResponsiveRecordsView
        title="Post Cosecha"
        subtitle="Secado, biomasa, rendimiento y registro químico real (% CBD y % THC hasta 100%)."
        items={items}
        columns={columns}
        dateAccessor={(p) => p.fecha_ini_secado}
        searchAccessor={(p) => `${loteById.get(p.lote_id) ?? ""} ${p.porcentaje_cbd} ${p.porcentaje_thc}`}
        loteIdAccessor={(p) => p.lote_id}
        canWrite={hasPermission("production:write")}
        canDelete={hasPermission("production:delete")}
        onNew={openNew}
        onEdit={openEdit}
        onDelete={(p) => void deleteEntityOfflineFirst("post_cosecha", p)}
        onTraceLot={(id) => setTraceId(id)}
        toast={toast}
        onDismissToast={() => setToast(null)}
      />

      <ModalDrawer
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Editar Post Cosecha" : "Nuevo Registro Post Cosecha"}
      >
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          <Field label="Registro de Cosecha (Id Lote)" htmlFor="pc-cos" required>
            <select
              id="pc-cos"
              required
              value={cosechaId}
              onChange={(e) => selectCosecha(e.target.value)}
              className={inputCls}
            >
              <option value="">Seleccione cosecha...</option>
              {cosechas.map((c) => (
                <option key={c.id} value={c.id}>
                  {loteById.get(c.lote_id) ?? "Lote"} • {c.fecha_cosecha} ({c.peso_verde} g verde)
                </option>
              ))}
            </select>
          </Field>

          {selectedCos && (
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div>
                <span className="text-slate-500">F. Cosecha</span>
                <p className="font-bold">{selectedCos.fecha_cosecha}</p>
              </div>
              <div>
                <span className="text-slate-500">N° Plantas</span>
                <p className="font-bold">{selectedCos.numero_plantas}</p>
              </div>
              <div>
                <span className="text-slate-500">Floración</span>
                <p className="font-bold">{selectedCos.dias_floracion} d</p>
              </div>
              <div>
                <span className="text-slate-500">Peso Verde Campo</span>
                <p className="font-bold text-emerald-800">{selectedCos.peso_verde} g</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="F.I Secado" htmlFor="pc-fini" required>
              <input id="pc-fini" type="date" required value={fIni} onChange={(e) => setFIni(e.target.value)} className={inputCls} />
            </Field>
            <Field label="F.F Secado" htmlFor="pc-ffin">
              <input id="pc-ffin" type="date" value={fFin} onChange={(e) => setFFin(e.target.value)} className={inputCls} />
            </Field>
            <Field label="Peso Flor Verde (g)" htmlFor="pc-pfv" required>
              <input id="pc-pfv" type="number" step="0.01" min={0.01} required value={pesoFlorVerde} onChange={(e) => setPesoFlorVerde(Number(e.target.value))} className={inputCls} />
            </Field>
            <Field label="Biomasa = Peso (g)" htmlFor="pc-bio">
              <input id="pc-bio" type="number" step="0.01" min={0} value={pesoBiomasa} onChange={(e) => setPesoBiomasa(Number(e.target.value))} className={inputCls} />
            </Field>
            <Field label="Peso Flor Seco (g)" htmlFor="pc-pfs" required>
              <input id="pc-pfs" type="number" step="0.01" min={0} required value={pesoFlorSeco} onChange={(e) => setPesoFlorSeco(Number(e.target.value))} className={inputCls} />
            </Field>
            <Field label="Rendimiento de Secado" htmlFor="pc-rend">
              <input id="pc-rend" readOnly value={`${calcularRendimientoSecado(pesoFlorVerde, pesoFlorSeco)}%`} className={inputCls} />
            </Field>
            <Field label="% CBD (0.00 - 100.00)" htmlFor="pc-cbd" required>
              <input id="pc-cbd" type="number" step="0.01" min={0} max={100} required value={cbd} onChange={(e) => setCbd(Number(e.target.value))} className={inputCls} />
            </Field>
            <Field label="% THC (0.00 - 100.00)" htmlFor="pc-thc" required>
              <input id="pc-thc" type="number" step="0.01" min={0} max={100} required value={thc} onChange={(e) => setThc(Number(e.target.value))} className={inputCls} />
            </Field>
          </div>
          <Field label="Observaciones" htmlFor="pc-obs">
            <textarea id="pc-obs" rows={2} value={obs} onChange={(e) => setObs(e.target.value)} className={inputCls} />
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
