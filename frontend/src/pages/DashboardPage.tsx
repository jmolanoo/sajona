import React, { useState } from "react";
import { Sprout, Package, TreePine, Scissors, FlaskConical, AlertOctagon, ArrowRight } from "lucide-react";
import { useEntityList, useSyncStatus } from "../db/useLocalData";
import { calcularSaldoVivoLote } from "../domain/calculations";
import type {
  Baja,
  Cosecha,
  PostCosecha,
  Propagacion,
  Transplante,
  Variedad,
} from "../domain/types";
import type { PageId } from "../components/AppShell";
import { LotTraceModal } from "../components/LotTraceModal";
import { SyncBadge } from "../components/UiPrimitives";

export function DashboardPage({ onNavigate }: { onNavigate: (p: PageId) => void }): React.ReactElement {
  const lotes = useEntityList<Propagacion>("propagacion").items;
  const transplantes = useEntityList<Transplante>("transplante").items;
  const cosechas = useEntityList<Cosecha>("cosecha").items;
  const postCosechas = useEntityList<PostCosecha>("post_cosecha").items;
  const bajas = useEntityList<Baja>("baja").items;
  const variedades = useEntityList<Variedad>("variedad").items;
  const syncStatus = useSyncStatus();
  const [traceLoteId, setTraceLoteId] = useState<string | null>(null);

  const varById = new Map(variedades.map((v) => [v.id, v.nombre]));
  const totalPlantasVivas = lotes.reduce((acc, l) => acc + calcularSaldoVivoLote(l, bajas), 0);
  const totalFlorSecaGr = postCosechas.reduce((acc, p) => acc + Number(p.peso_flor_seco || 0), 0);
  const avgCbd =
    postCosechas.length > 0
      ? (
          postCosechas.reduce((a, p) => a + Number(p.porcentaje_cbd || 0), 0) /
          postCosechas.length
        ).toFixed(2)
      : "0.00";

  const cards = [
    {
      label: "Lotes Activos",
      value: lotes.length,
      sub: `${totalPlantasVivas} unidades vivas`,
      icon: Sprout,
      color: "bg-emerald-50 text-emerald-800 border-emerald-200",
      page: "propagacion" as PageId,
    },
    {
      label: "Trasplantes",
      value: transplantes.length,
      sub: "Bolsa y Campo",
      icon: Package,
      color: "bg-blue-50 text-blue-800 border-blue-200",
      page: "transplante_bolsa" as PageId,
    },
    {
      label: "Cosechas",
      value: cosechas.length,
      sub: `${cosechas.reduce((a, c) => a + Number(c.peso_verde || 0), 0).toLocaleString("es-CO")} g verde`,
      icon: Scissors,
      color: "bg-amber-50 text-amber-900 border-amber-200",
      page: "cosecha" as PageId,
    },
    {
      label: "Post Cosecha",
      value: `${totalFlorSecaGr.toLocaleString("es-CO")} g`,
      sub: `CBD prom. ${avgCbd}%`,
      icon: FlaskConical,
      color: "bg-purple-50 text-purple-900 border-purple-200",
      page: "post_cosecha" as PageId,
    },
  ];

  const quickActions: Array<{ label: string; page: PageId; icon: React.ComponentType<{ className?: string }> }> = [
    { label: "Nuevo Lote Propagación", page: "propagacion", icon: Sprout },
    { label: "Transplante a Bolsa", page: "transplante_bolsa", icon: Package },
    { label: "Extracción Planta Madre", page: "planta_madre", icon: TreePine },
    { label: "Registrar Baja", page: "bajas", icon: AlertOctagon },
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">
            Panel Operativo SAJONA
          </h1>
          <p className="text-xs sm:text-sm text-slate-600">
            Trazabilidad por lotes desde propagación hasta análisis de cannabinoides ({syncStatus.isOnline ? "Conectado" : "Trabajando sin conexión"}).
          </p>
        </div>
      </div>

      {/* KPIs Mobile-First */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <button
              key={c.label}
              type="button"
              onClick={() => onNavigate(c.page)}
              className={`text-left rounded-2xl border p-4 shadow-sm hover:shadow transition ${c.color}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wide">{c.label}</span>
                <Icon className="h-5 w-5 opacity-80" />
              </div>
              <p className="mt-2 text-2xl font-extrabold">{c.value}</p>
              <p className="mt-0.5 text-xs opacity-85">{c.sub}</p>
            </button>
          );
        })}
      </div>

      {/* Accesos rápidos táctiles */}
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 mb-3">Acciones rápidas en campo</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {quickActions.map((qa) => {
            const Icon = qa.icon;
            return (
              <button
                key={qa.label}
                type="button"
                onClick={() => onNavigate(qa.page)}
                className="min-h-[48px] flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 hover:bg-slate-100"
              >
                <span className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-red-800" />
                  {qa.label}
                </span>
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </button>
            );
          })}
        </div>
      </section>

      {/* Lotes recientes con trazabilidad 360 */}
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-slate-900">Trazabilidad por Lote (Local / Offline)</h2>
          <button
            type="button"
            onClick={() => onNavigate("reportes")}
            className="text-xs font-bold text-red-800 hover:underline"
          >
            Ir a Reportes
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {lotes.map((l) => {
            const vivo = calcularSaldoVivoLote(l, bajas);
            return (
              <div
                key={l.id}
                className="rounded-xl border border-slate-200 p-3.5 flex items-center justify-between gap-3 hover:bg-slate-50"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-slate-900">{l.codigo_lote}</span>
                    <SyncBadge status={l._local_sync_status} />
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5 truncate">
                    {varById.get(l.variedad_id) ?? "Variedad"} • Siembra: {l.fecha_siembra} • Saldo:{" "}
                    <strong>
                      {vivo}/{l.cantidad_material}
                    </strong>
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setTraceLoteId(l.id)}
                  className="shrink-0 min-h-[40px] rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-bold text-white hover:bg-slate-800"
                >
                  Ver Traza
                </button>
              </div>
            );
          })}
        </div>
      </section>

      <LotTraceModal loteId={traceLoteId} onClose={() => setTraceLoteId(null)} />
    </div>
  );
}
