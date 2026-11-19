import React, { useMemo, useState } from "react";
import { Plus, Search, Pencil, Trash2, GitBranch } from "lucide-react";
import { exportToExcel, exportToPdf, exportToText, type ExportColumn } from "../utils/exporters";
import type { BaseEntity } from "../domain/types";
import { ExportBar, SyncBadge, ToastBanner, inputCls } from "./UiPrimitives";

export interface ColumnDef<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  exportValue: (item: T) => string | number;
  mobilePrimary?: boolean;
}

export function ResponsiveRecordsView<T extends BaseEntity>({
  title,
  subtitle,
  items,
  columns,
  dateAccessor,
  searchAccessor,
  loteIdAccessor,
  canWrite,
  canDelete,
  onNew,
  onEdit,
  onDelete,
  onTraceLot,
  toast,
  onDismissToast,
  extraHeader,
}: {
  title: string;
  subtitle: string;
  items: T[];
  columns: ColumnDef<T>[];
  dateAccessor?: (item: T) => string;
  searchAccessor: (item: T) => string;
  loteIdAccessor?: (item: T) => string;
  canWrite: boolean;
  canDelete: boolean;
  onNew?: () => void;
  onEdit?: (item: T) => void;
  onDelete?: (item: T) => void;
  onTraceLot?: (loteId: string) => void;
  toast: { type: "success" | "error" | "warning"; text: string } | null;
  onDismissToast: () => void;
  extraHeader?: React.ReactNode;
}): React.ReactElement {
  const [search, setSearch] = useState("");
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return items.filter((item) => {
      if (q && !searchAccessor(item).toLowerCase().includes(q)) return false;
      if (dateAccessor && (fechaInicio || fechaFin)) {
        const d = dateAccessor(item);
        if (fechaInicio && d < fechaInicio) return false;
        if (fechaFin && d > fechaFin) return false;
      }
      return true;
    });
  }, [items, search, fechaInicio, fechaFin, dateAccessor, searchAccessor]);

  const exportCols: ExportColumn[] = columns.map((c) => ({ key: c.key, header: c.header }));
  const exportRows = filtered.map((item) => {
    const obj: Record<string, unknown> = {};
    for (const c of columns) {
      obj[c.key] = c.exportValue(item);
    }
    return obj;
  });
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "_");

  return (
    <div className="space-y-4">
      <ToastBanner toast={toast} onDismiss={onDismissToast} />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">{title}</h1>
          <p className="text-xs sm:text-sm text-slate-600">{subtitle}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 no-print">
          <ExportBar
            onExcel={() => void exportToExcel(title, exportCols, exportRows, slug)}
            onTxt={() => exportToText(title, exportCols, exportRows, slug)}
            onPdf={() => void exportToPdf(title, exportCols, exportRows, slug)}
            onPrint={() => window.print()}
          />
          {canWrite && onNew && (
            <button
              type="button"
              onClick={onNew}
              className="inline-flex min-h-[44px] items-center gap-1.5 rounded-xl bg-emerald-700 px-4 py-2 text-sm font-bold text-white shadow-sm hover:bg-emerald-800 active:bg-emerald-900"
            >
              <Plus className="h-4 w-4" />
              <span>Nuevo</span>
            </button>
          )}
        </div>
      </div>

      {extraHeader}

      {/* Filtros Mobile-First */}
      <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm no-print">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <div className="relative">
            <Search className="absolute left-3 top-3.5 h-4 w-4 text-slate-400" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por lote, variedad, estado..."
              aria-label="Buscar registros"
              className={`${inputCls} pl-9`}
            />
          </div>
          {dateAccessor && (
            <>
              <input
                type="date"
                value={fechaInicio}
                onChange={(e) => setFechaInicio(e.target.value)}
                aria-label="Fecha inicial"
                className={inputCls}
              />
              <input
                type="date"
                value={fechaFin}
                onChange={(e) => setFechaFin(e.target.value)}
                aria-label="Fecha final"
                className={inputCls}
              />
            </>
          )}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
          <p className="text-sm font-semibold text-slate-700">No hay registros para mostrar</p>
          <p className="text-xs text-slate-500 mt-1">
            Ajusta los filtros de búsqueda o registra un nuevo movimiento.
          </p>
        </div>
      ) : (
        <>
          {/* Vista Mobile-First en Tarjetas (< md) */}
          <div className="grid grid-cols-1 gap-3 md:hidden">
            {filtered.map((item) => (
              <article
                key={item.id}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-2.5"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="font-bold text-slate-900 text-base">
                    {columns[0]?.render(item)}
                  </div>
                  <SyncBadge status={item._local_sync_status} />
                </div>
                <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
                  {columns.slice(1).map((col) => (
                    <div key={col.key}>
                      <dt className="text-slate-500 font-medium">{col.header}</dt>
                      <dd className="text-slate-900 font-semibold">{col.render(item)}</dd>
                    </div>
                  ))}
                </dl>
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 no-print">
                  {onTraceLot && loteIdAccessor && (
                    <button
                      type="button"
                      onClick={() => onTraceLot(loteIdAccessor(item))}
                      className="inline-flex min-h-[38px] items-center gap-1 rounded-lg border border-slate-300 px-3 text-xs font-semibold text-slate-800 hover:bg-slate-100"
                    >
                      <GitBranch className="h-3.5 w-3.5 text-emerald-700" />
                      Trazabilidad
                    </button>
                  )}
                  {canWrite && onEdit && (
                    <button
                      type="button"
                      onClick={() => onEdit(item)}
                      className="inline-flex min-h-[38px] items-center gap-1 rounded-lg border border-slate-300 px-3 text-xs font-semibold text-slate-800 hover:bg-slate-100"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      Editar
                    </button>
                  )}
                  {canDelete && onDelete && (
                    <button
                      type="button"
                      onClick={() => onDelete(item)}
                      className="inline-flex min-h-[38px] items-center gap-1 rounded-lg border border-red-200 px-3 text-xs font-semibold text-red-800 hover:bg-red-50"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Eliminar
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>

          {/* Vista Tabla Desktop (>= md) */}
          <div className="hidden md:block overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-100">
                <tr>
                  {columns.map((col) => (
                    <th
                      key={col.key}
                      scope="col"
                      className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-700"
                    >
                      {col.header}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-700">
                    Sync
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-700 no-print">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50">
                    {columns.map((col) => (
                      <td key={col.key} className="px-4 py-3 text-slate-800 whitespace-nowrap">
                        {col.render(item)}
                      </td>
                    ))}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <SyncBadge status={item._local_sync_status} />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right space-x-2 no-print">
                      {onTraceLot && loteIdAccessor && (
                        <button
                          type="button"
                          onClick={() => onTraceLot(loteIdAccessor(item))}
                          className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-2.5 py-1 text-xs font-semibold text-slate-800 hover:bg-slate-100"
                          title="Ver trazabilidad"
                        >
                          <GitBranch className="h-3.5 w-3.5 text-emerald-700" />
                          Traza
                        </button>
                      )}
                      {canWrite && onEdit && (
                        <button
                          type="button"
                          onClick={() => onEdit(item)}
                          className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-2.5 py-1 text-xs font-semibold text-slate-800 hover:bg-slate-100"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                          Editar
                        </button>
                      )}
                      {canDelete && onDelete && (
                        <button
                          type="button"
                          onClick={() => onDelete(item)}
                          className="inline-flex items-center gap-1 rounded-lg border border-red-200 px-2.5 py-1 text-xs font-semibold text-red-800 hover:bg-red-50"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Eliminar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
