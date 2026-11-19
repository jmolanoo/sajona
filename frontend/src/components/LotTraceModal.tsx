import React, { useEffect, useState } from "react";
import { db } from "../db/schema";
import { calcularSaldoVivoLote } from "../domain/calculations";
import type {
  Baja,
  ControlFase,
  Cosecha,
  ExtraccionMaterial,
  PlantaMadre,
  PostCosecha,
  Propagacion,
  Transplante,
} from "../domain/types";
import { ModalDrawer } from "./UiPrimitives";

interface TraceState {
  lote: Propagacion;
  saldoVivo: number;
  bajasTotal: number;
  transplantes: Transplante[];
  madres: PlantaMadre[];
  extracciones: ExtraccionMaterial[];
  controles: ControlFase[];
  cosechas: Cosecha[];
  postCosechas: PostCosecha[];
  bajas: Baja[];
}

export function LotTraceModal({
  loteId,
  onClose,
}: {
  loteId: string | null;
  onClose: () => void;
}): React.ReactElement | null {
  const [trace, setTrace] = useState<TraceState | null>(null);

  useEffect(() => {
    if (!loteId) {
      setTrace(null);
      return;
    }
    void (async () => {
      const lote = await db.propagaciones.get(loteId);
      if (!lote) return;
      const [transplantes, madres, extracciones, controles, cosechas, postCosechas, bajas] =
        await Promise.all([
          db.transplantes.where("lote_id").equals(loteId).filter((r) => !r.deleted_at).toArray(),
          db.plantas_madre.where("lote_id").equals(loteId).filter((r) => !r.deleted_at).toArray(),
          db.extracciones_material.where("lote_id").equals(loteId).filter((r) => !r.deleted_at).toArray(),
          db.controles_fase.where("lote_id").equals(loteId).filter((r) => !r.deleted_at).toArray(),
          db.cosechas.where("lote_id").equals(loteId).filter((r) => !r.deleted_at).toArray(),
          db.post_cosechas.where("lote_id").equals(loteId).filter((r) => !r.deleted_at).toArray(),
          db.bajas.where("lote_id").equals(loteId).filter((r) => !r.deleted_at).toArray(),
        ]);
      const bajasTotal = bajas.reduce((acc, b) => acc + Number(b.cantidad || 0), 0);
      setTrace({
        lote,
        saldoVivo: calcularSaldoVivoLote(lote, bajas),
        bajasTotal,
        transplantes,
        madres,
        extracciones,
        controles,
        cosechas,
        postCosechas,
        bajas,
      });
    })();
  }, [loteId]);

  if (!loteId) return null;

  return (
    <ModalDrawer
      open={Boolean(loteId)}
      onClose={onClose}
      title={`Trazabilidad Integral — ${trace?.lote.codigo_lote ?? "Lote"}`}
      subtitle="Consulta local disponible con y sin conexión a Internet."
    >
      {!trace ? (
        <p className="text-sm text-slate-600">Cargando cadena productiva...</p>
      ) : (
        <div className="space-y-4 text-sm">
          <div className="grid grid-cols-3 gap-2.5">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <span className="text-xs text-slate-600">Inicial</span>
              <p className="text-lg font-bold text-slate-900">{trace.lote.cantidad_material}</p>
            </div>
            <div className="rounded-xl border border-red-200 bg-red-50 p-3">
              <span className="text-xs text-red-800">Bajas</span>
              <p className="text-lg font-bold text-red-900">{trace.bajasTotal}</p>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3">
              <span className="text-xs text-emerald-800">Saldo Vivo</span>
              <p className="text-lg font-bold text-emerald-900">{trace.saldoVivo}</p>
            </div>
          </div>

          <section className="rounded-xl border border-slate-200 p-3 space-y-1">
            <h3 className="font-bold text-slate-900">1. Propagación</h3>
            <p className="text-xs text-slate-700">
              Siembra: {trace.lote.fecha_siembra} • Tipo: {trace.lote.tipo_propagacion} • Origen:{" "}
              {trace.lote.tipo_incorporacion} • Estado: {trace.lote.estado}
            </p>
          </section>

          <section className="rounded-xl border border-slate-200 p-3 space-y-1">
            <h3 className="font-bold text-slate-900">
              2. Trasplantes ({trace.transplantes.length})
            </h3>
            {trace.transplantes.length === 0 ? (
              <p className="text-xs text-slate-500">Sin trasplantes registrados.</p>
            ) : (
              trace.transplantes.map((t) => (
                <p key={t.id} className="text-xs text-slate-700">
                  [{t.etapa}] {t.fecha_transplante} • {t.tipo_lote} • Buenas: {t.cantidad_buenas} (
                  {t.porcentaje_buenas}%) • Malas: {t.cantidad_malas} ({t.porcentaje_malas}%)
                </p>
              ))
            )}
          </section>

          <section className="rounded-xl border border-slate-200 p-3 space-y-1">
            <h3 className="font-bold text-slate-900">
              3. Plantas Madre ({trace.madres.length}) y Extracciones ({trace.extracciones.length})
            </h3>
            <p className="text-xs text-slate-700">
              Total Esquejes extraídos:{" "}
              {trace.extracciones.reduce((a, e) => a + e.cantidad_esquejes, 0)} • Total Semillas:{" "}
              {trace.extracciones.reduce((a, e) => a + e.cantidad_semillas, 0)}
            </p>
          </section>

          <section className="rounded-xl border border-slate-200 p-3 space-y-1">
            <h3 className="font-bold text-slate-900">
              4. Controles e Historia Clínica ({trace.controles.length})
            </h3>
            {trace.controles.map((c) => (
              <p key={c.id} className="text-xs text-slate-700">
                {c.fecha_inicio} • Fase {c.fase_cultivo} • Estado: {c.estado_revision} •{" "}
                {c.tratamiento_aplicado || c.observaciones}
              </p>
            ))}
          </section>

          <section className="rounded-xl border border-slate-200 p-3 space-y-1">
            <h3 className="font-bold text-slate-900">
              5. Cosecha ({trace.cosechas.length}) y Post Cosecha ({trace.postCosechas.length})
            </h3>
            {trace.cosechas.map((c) => (
              <p key={c.id} className="text-xs text-slate-700">
                Cosecha {c.fecha_cosecha} • Cama {c.cama || "N/A"} • Plantas: {c.numero_plantas} •
                Peso verde: {c.peso_verde} g
              </p>
            ))}
            {trace.postCosechas.map((p) => (
              <p key={p.id} className="text-xs font-medium text-emerald-900">
                Secado {p.fecha_ini_secado} → {p.fecha_fin_secado || "En curso"} • Flor seca:{" "}
                {p.peso_flor_seco} g • CBD: {p.porcentaje_cbd}% • THC: {p.porcentaje_thc}%
              </p>
            ))}
          </section>
        </div>
      )}
    </ModalDrawer>
  );
}
