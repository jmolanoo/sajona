import React, { useState } from "react";
import { Plus, Sprout } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { ResponsiveRecordsView, type ColumnDef } from "../components/ResponsiveRecordsView";
import { Field, ModalDrawer, inputCls } from "../components/UiPrimitives";
import { saveEntityOfflineFirst, useEntityList } from "../db/useLocalData";
import type {
  ExtraccionMaterial,
  PlantaMadre,
  Propagacion,
  Transplante,
  Variedad,
} from "../domain/types";

export function PlantaMadrePage(): React.ReactElement {
  const { hasPermission } = useAuth();
  const lotes = useEntityList<Propagacion>("propagacion").items;
  const transplantes = useEntityList<Transplante>("transplante").items;
  const madres = useEntityList<PlantaMadre>("planta_madre").items;
  const extracciones = useEntityList<ExtraccionMaterial>("extraccion_material").items;
  const variedades = useEntityList<Variedad>("variedad").items;

  const [selectedLote, setSelectedLote] = useState<Propagacion | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);

  const [numPlanta, setNumPlanta] = useState("");
  const [fechaExt, setFechaExt] = useState(new Date().toISOString().slice(0, 10));
  const [fase, setFase] = useState("ENRAIZAMIENTO");
  const [cantEsq, setCantEsq] = useState(10);
  const [cantSem, setCantSem] = useState(0);
  const [obs, setObs] = useState("");

  const varById = new Map(variedades.map((v) => [v.id, v.nombre]));
  const madreLoteIds = new Set(
    transplantes.filter((t) => t.tipo_lote === "PLANTA_MADRE").map((t) => t.lote_id)
  );
  const lotesMadre = lotes.filter(
    (l) => madreLoteIds.has(l.id) || l.estado === "PLANTA_MADRE" || l.cantidad_plantas_madre > 0
  );

  const tpByLote = new Map<string, Transplante>();
  for (const t of transplantes) {
    if (t.tipo_lote === "PLANTA_MADRE") tpByLote.set(t.lote_id, t);
  }

  const loteExts = selectedLote ? extracciones.filter((e) => e.lote_id === selectedLote.id) : [];
  const loteMadres = selectedLote ? madres.filter((m) => m.lote_id === selectedLote.id) : [];
  const totalEsq = loteExts.reduce((a, e) => a + e.cantidad_esquejes, 0);
  const totalSem = loteExts.reduce((a, e) => a + e.cantidad_semillas, 0);

  const handleAddExtraccion = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!selectedLote) return;
    try {
      if (cantEsq <= 0 && cantSem <= 0) {
        throw new Error("Ingrese al menos 1 esqueje o 1 semilla.");
      }
      const existsMadre = loteMadres.find((m) => m.numero_planta === numPlanta.trim());
      let madreId = existsMadre?.id ?? null;
      if (!madreId) {
        madreId = await saveEntityOfflineFirst("planta_madre", {
          lote_id: selectedLote.id,
          numero_planta: numPlanta.trim(),
          fecha_siembra: selectedLote.fecha_siembra,
          lugar_siembra: "Área Plantas Madre",
          estado: "ACTIVA",
        });
      }
      await saveEntityOfflineFirst("extraccion_material", {
        lote_id: selectedLote.id,
        planta_madre_id: madreId,
        numero_planta_madre: numPlanta.trim(),
        fecha_extraccion: fechaExt,
        fase,
        cantidad_esquejes: Number(cantEsq),
        cantidad_semillas: Number(cantSem),
        observaciones: obs.trim(),
      });
      setNumPlanta("");
      setObs("");
      setToast({ type: "success", text: "Extracción de esquejes/semillas registrada." });
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error al registrar." });
    }
  };

  const handleDerivarLote = async (): Promise<void> => {
    if (!selectedLote) return;
    try {
      const code = `LOT-${new Date().getFullYear()}-H${Math.floor(100 + Math.random() * 899)}`;
      const qty = Math.max(totalEsq + totalSem, 10);
      await saveEntityOfflineFirst("propagacion", {
        codigo_lote: code,
        fecha_siembra: new Date().toISOString().slice(0, 10),
        tipo_propagacion: totalEsq >= totalSem ? "ESQUEJE" : "SEMILLA",
        variedad_id: selectedLote.variedad_id,
        tipo_incorporacion: "PROPIA",
        cantidad_material: qty,
        cantidad_plantas_madre: 0,
        lote_origen_id: selectedLote.id,
        observaciones: `Derivado desde lote madre ${selectedLote.codigo_lote}`,
        estado: "PROPAGACION",
      });
      setToast({ type: "success", text: `Nuevo lote hijo ${code} creado en Propagación.` });
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error al derivar." });
    }
  };

  const columns: ColumnDef<Propagacion>[] = [
    {
      key: "codigo",
      header: "Id Lote",
      render: (l) => <span className="font-bold">{l.codigo_lote}</span>,
      exportValue: (l) => l.codigo_lote,
    },
    {
      key: "variedad",
      header: "Variedad",
      render: (l) => varById.get(l.variedad_id) ?? "—",
      exportValue: (l) => varById.get(l.variedad_id) ?? "",
    },
    {
      key: "fecha_prop",
      header: "F. Propagación",
      render: (l) => l.fecha_siembra,
      exportValue: (l) => l.fecha_siembra,
    },
    {
      key: "fecha_tp",
      header: "F. Transplante",
      render: (l) => tpByLote.get(l.id)?.fecha_transplante ?? "—",
      exportValue: (l) => tpByLote.get(l.id)?.fecha_transplante ?? "",
    },
    {
      key: "buenas",
      header: "Cant. Buenas",
      render: (l) => tpByLote.get(l.id)?.cantidad_buenas ?? l.cantidad_material,
      exportValue: (l) => tpByLote.get(l.id)?.cantidad_buenas ?? l.cantidad_material,
    },
    {
      key: "totales",
      header: "Esquejes / Semillas",
      render: (l) => {
        const exts = extracciones.filter((e) => e.lote_id === l.id);
        const esq = exts.reduce((a, e) => a + e.cantidad_esquejes, 0);
        const sem = exts.reduce((a, e) => a + e.cantidad_semillas, 0);
        return (
          <button
            type="button"
            onClick={() => setSelectedLote(l)}
            className="rounded-lg bg-red-50 border border-red-200 px-2.5 py-1 text-xs font-bold text-red-900 hover:bg-red-100"
          >
            {esq} Esq / {sem} Sem • Gestionar
          </button>
        );
      },
      exportValue: (l) => {
        const exts = extracciones.filter((e) => e.lote_id === l.id);
        return `${exts.reduce((a, e) => a + e.cantidad_esquejes, 0)} / ${exts.reduce(
          (a, e) => a + e.cantidad_semillas,
          0
        )}`;
      },
    },
  ];

  return (
    <>
      <ResponsiveRecordsView
        title="Planta Madre y Extracción"
        subtitle="Control de lotes madre y contabilidad acumulada de esquejes y semillas (CV-02 / CV-09)."
        items={lotesMadre}
        columns={columns}
        dateAccessor={(l) => l.fecha_siembra}
        searchAccessor={(l) => `${l.codigo_lote} ${varById.get(l.variedad_id) ?? ""}`}
        canWrite={false}
        canDelete={false}
        onEdit={(l) => setSelectedLote(l)}
        toast={toast}
        onDismissToast={() => setToast(null)}
      />

      <ModalDrawer
        open={Boolean(selectedLote)}
        onClose={() => setSelectedLote(null)}
        title={`Lote ${selectedLote?.codigo_lote ?? ""} — Esquejes y Semillas`}
        subtitle={`Fecha Transplante: ${
          selectedLote ? tpByLote.get(selectedLote.id)?.fecha_transplante ?? "N/A" : ""
        }`}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3">
              <span className="text-xs font-semibold text-emerald-800">Total Lote Esquejes</span>
              <p className="text-2xl font-extrabold text-emerald-900">{totalEsq}</p>
            </div>
            <div className="rounded-xl bg-amber-50 border border-amber-200 p-3">
              <span className="text-xs font-semibold text-amber-900">Total Lote Semillas</span>
              <p className="text-2xl font-extrabold text-amber-900">{totalSem}</p>
            </div>
          </div>

          {hasPermission("production:write") && (
            <form onSubmit={(e) => void handleAddExtraccion(e)} className="rounded-xl border border-slate-200 bg-slate-50 p-3.5 space-y-3">
              <p className="text-xs font-bold uppercase text-slate-700">Registrar Extracción</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                <Field label="Número Planta Madre" htmlFor="pm-num" required>
                  <input
                    id="pm-num"
                    required
                    placeholder="ej. 15"
                    value={numPlanta}
                    onChange={(e) => setNumPlanta(e.target.value)}
                    className={inputCls}
                  />
                </Field>
                <Field label="Fecha Esqueje" htmlFor="pm-fecha" required>
                  <input
                    id="pm-fecha"
                    type="date"
                    required
                    value={fechaExt}
                    onChange={(e) => setFechaExt(e.target.value)}
                    className={inputCls}
                  />
                </Field>
                <Field label="Fase" htmlFor="pm-fase">
                  <select
                    id="pm-fase"
                    value={fase}
                    onChange={(e) => setFase(e.target.value)}
                    className={inputCls}
                  >
                    <option value="CUBICULO">Cubículo</option>
                    <option value="ENRAIZAMIENTO">Enraizamiento</option>
                    <option value="BOLSA">Bolsa</option>
                    <option value="ALMACENAMIENTO">Almacenamiento</option>
                    <option value="SIEMBRA_SEMILLA">Siembra Semilla</option>
                  </select>
                </Field>
                <Field label="Cant. Esquejes" htmlFor="pm-esq">
                  <input
                    id="pm-esq"
                    type="number"
                    min={0}
                    value={cantEsq}
                    onChange={(e) => setCantEsq(Number(e.target.value))}
                    className={inputCls}
                  />
                </Field>
                <Field label="Cant. Semillas" htmlFor="pm-sem">
                  <input
                    id="pm-sem"
                    type="number"
                    min={0}
                    value={cantSem}
                    onChange={(e) => setCantSem(Number(e.target.value))}
                    className={inputCls}
                  />
                </Field>
                <Field label="Observación" htmlFor="pm-obs">
                  <input
                    id="pm-obs"
                    value={obs}
                    onChange={(e) => setObs(e.target.value)}
                    className={inputCls}
                  />
                </Field>
              </div>
              <div className="flex flex-wrap justify-between gap-2">
                <button
                  type="button"
                  onClick={() => void handleDerivarLote()}
                  className="inline-flex min-h-[40px] items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 text-xs font-bold text-slate-800 hover:bg-slate-100"
                >
                  <Sprout className="h-4 w-4 text-emerald-700" />
                  Derivar Nuevo Lote en Propagación
                </button>
                <button
                  type="submit"
                  className="inline-flex min-h-[40px] items-center gap-1.5 rounded-lg bg-emerald-700 px-4 text-xs font-bold text-white hover:bg-emerald-800"
                >
                  <Plus className="h-4 w-4" />
                  Guardar Extracción
                </button>
              </div>
            </form>
          )}

          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-100">
                <tr>
                  <th className="px-3 py-2 text-left font-bold">Número Planta Madre</th>
                  <th className="px-3 py-2 text-left font-bold">Fecha</th>
                  <th className="px-3 py-2 text-left font-bold">Cant. Esquejes</th>
                  <th className="px-3 py-2 text-left font-bold">Cant. Semillas</th>
                  <th className="px-3 py-2 text-left font-bold">Fase</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {loteExts.map((e) => (
                  <tr key={e.id}>
                    <td className="px-3 py-2 font-bold">{e.numero_planta_madre}</td>
                    <td className="px-3 py-2">{e.fecha_extraccion}</td>
                    <td className="px-3 py-2">{e.cantidad_esquejes}</td>
                    <td className="px-3 py-2">{e.cantidad_semillas}</td>
                    <td className="px-3 py-2">{e.fase}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </ModalDrawer>
    </>
  );
}
