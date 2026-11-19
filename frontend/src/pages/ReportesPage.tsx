import React, { useMemo, useState } from "react";
import { ExportBar, Field, inputCls } from "../components/UiPrimitives";
import { useEntityList } from "../db/useLocalData";
import { calcularRendimientoSecado, calcularSaldoVivoLote } from "../domain/calculations";
import type { Baja, Cosecha, PostCosecha, Propagacion, Transplante, Variedad } from "../domain/types";
import { exportToExcel, exportToPdf, exportToText, type ExportColumn } from "../utils/exporters";

export function ReportesPage(): React.ReactElement {
  const lotes = useEntityList<Propagacion>("propagacion").items;
  const variedades = useEntityList<Variedad>("variedad").items;
  const transplantes = useEntityList<Transplante>("transplante").items;
  const cosechas = useEntityList<Cosecha>("cosecha").items;
  const postCosechas = useEntityList<PostCosecha>("post_cosecha").items;
  const bajas = useEntityList<Baja>("baja").items;

  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [codigoLoteFilter, setCodigoLoteFilter] = useState("");

  const varById = new Map(variedades.map((v) => [v.id, v.nombre]));

  const rows = useMemo(() => {
    const q = codigoLoteFilter.trim().toLowerCase();
    return lotes
      .filter((l) => {
        if (q && !l.codigo_lote.toLowerCase().includes(q)) return false;
        if (fechaInicio && l.fecha_siembra < fechaInicio) return false;
        if (fechaFin && l.fecha_siembra > fechaFin) return false;
        return true;
      })
      .map((l) => {
        const loteTp = transplantes.filter((t) => t.lote_id === l.id);
        const loteCos = cosechas.filter((c) => c.lote_id === l.id);
        const lotePost = postCosechas.filter((p) => p.lote_id === l.id);
        const bajasCount = l.cantidad_material - calcularSaldoVivoLote(l, bajas);
        const pesoVerde = loteCos.reduce((a, c) => a + Number(c.peso_verde || 0), 0);
        const pesoSeco = lotePost.reduce((a, p) => a + Number(p.peso_flor_seco || 0), 0);
        const cbd = lotePost[0]?.porcentaje_cbd ?? 0;
        const thc = lotePost[0]?.porcentaje_thc ?? 0;
        return {
          codigo_lote: l.codigo_lote,
          fecha_siembra: l.fecha_siembra,
          variedad: varById.get(l.variedad_id) ?? "—",
          inicial: l.cantidad_material,
          bajas: bajasCount,
          saldo_vivo: calcularSaldoVivoLote(l, bajas),
          trasplantes: loteTp.length,
          peso_verde_g: pesoVerde,
          peso_seco_g: pesoSeco,
          rendimiento_pct: `${calcularRendimientoSecado(pesoVerde, pesoSeco)}%`,
          cbd_pct: `${cbd}%`,
          thc_pct: `${thc}%`,
        };
      });
  }, [lotes, variedades, transplantes, cosechas, postCosechas, bajas, fechaInicio, fechaFin, codigoLoteFilter]);

  const cols: ExportColumn[] = [
    { key: "codigo_lote", header: "Id Lote" },
    { key: "fecha_siembra", header: "Fecha Siembra" },
    { key: "variedad", header: "Variedad" },
    { key: "inicial", header: "Cant. Inicial" },
    { key: "bajas", header: "Bajas" },
    { key: "saldo_vivo", header: "Saldo Vivo" },
    { key: "peso_verde_g", header: "Peso Verde (g)" },
    { key: "peso_seco_g", header: "Flor Seca (g)" },
    { key: "cbd_pct", header: "% CBD" },
    { key: "thc_pct", header: "% THC" },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">Reportes y Trazabilidad</h1>
          <p className="text-xs sm:text-sm text-slate-600">
            Consolidado por fechas e Id Lote con exportación local en Excel, Texto y PDF (funciona sin conexión).
          </p>
        </div>
        <ExportBar
          onExcel={() => void exportToExcel("Reporte Consolidado SAJONA", cols, rows, "sajona_reporte_lotes")}
          onTxt={() => exportToText("Reporte Consolidado SAJONA", cols, rows, "sajona_reporte_lotes")}
          onPdf={() => void exportToPdf("Reporte Consolidado SAJONA", cols, rows, "sajona_reporte_lotes")}
          onPrint={() => window.print()}
        />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm grid grid-cols-1 sm:grid-cols-3 gap-3 no-print">
        <Field label="Fecha de Inicio" htmlFor="rep-fini">
          <input id="rep-fini" type="date" value={fechaInicio} onChange={(e) => setFechaInicio(e.target.value)} className={inputCls} />
        </Field>
        <Field label="Fecha de Fin" htmlFor="rep-ffin">
          <input id="rep-ffin" type="date" value={fechaFin} onChange={(e) => setFechaFin(e.target.value)} className={inputCls} />
        </Field>
        <Field label="Id Lote" htmlFor="rep-lote">
          <input id="rep-lote" value={codigoLoteFilter} onChange={(e) => setCodigoLoteFilter(e.target.value)} placeholder="ej. LOT-2026-031" className={inputCls} />
        </Field>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-xs sm:text-sm">
          <thead className="bg-slate-100">
            <tr>
              {cols.map((c) => (
                <th key={c.key} className="px-3 py-3 text-left text-xs font-bold uppercase text-slate-700">
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {rows.map((r) => (
              <tr key={r.codigo_lote} className="hover:bg-slate-50">
                <td className="px-3 py-2.5 font-bold">{r.codigo_lote}</td>
                <td className="px-3 py-2.5">{r.fecha_siembra}</td>
                <td className="px-3 py-2.5">{r.variedad}</td>
                <td className="px-3 py-2.5">{r.inicial}</td>
                <td className="px-3 py-2.5 text-red-700 font-semibold">{r.bajas}</td>
                <td className="px-3 py-2.5 text-emerald-800 font-semibold">{r.saldo_vivo}</td>
                <td className="px-3 py-2.5">{r.peso_verde_g}</td>
                <td className="px-3 py-2.5">{r.peso_seco_g}</td>
                <td className="px-3 py-2.5">{r.cbd_pct}</td>
                <td className="px-3 py-2.5">{r.thc_pct}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
