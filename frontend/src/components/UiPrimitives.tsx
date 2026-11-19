import React from "react";
import { FileSpreadsheet, FileText, Printer, FileDown, X, AlertCircle, CheckCircle2 } from "lucide-react";
import type { LocalSyncStatus } from "../domain/types";

export function SyncBadge({ status }: { status?: LocalSyncStatus }): React.ReactElement | null {
  if (!status || status === "synced") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
        Sincronizado
      </span>
    );
  }
  if (status === "conflict") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-semibold text-red-800 border border-red-300">
        <AlertCircle className="h-3.5 w-3.5" />
        Conflicto
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-900 border border-amber-300">
      <span className="h-1.5 w-1.5 rounded-full bg-amber-600 animate-pulse" />
      Pendiente
    </span>
  );
}

export function ExportBar({
  onExcel,
  onTxt,
  onPdf,
  onPrint,
}: {
  onExcel: () => void;
  onTxt: () => void;
  onPdf: () => void;
  onPrint?: () => void;
}): React.ReactElement {
  const btnCls =
    "inline-flex min-h-[40px] items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-100 active:bg-slate-200 transition";
  return (
    <div className="flex flex-wrap items-center gap-2 no-print" role="group" aria-label="Exportación">
      <button type="button" onClick={onExcel} className={btnCls} title="Exportar Excel">
        <FileSpreadsheet className="h-4 w-4 text-emerald-700" />
        <span>Excel</span>
      </button>
      <button type="button" onClick={onTxt} className={btnCls} title="Exportar Texto">
        <FileText className="h-4 w-4 text-slate-700" />
        <span>TXT</span>
      </button>
      <button type="button" onClick={onPdf} className={btnCls} title="Exportar PDF">
        <FileDown className="h-4 w-4 text-red-700" />
        <span>PDF</span>
      </button>
      {onPrint && (
        <button type="button" onClick={onPrint} className={btnCls} title="Imprimir">
          <Printer className="h-4 w-4 text-blue-700" />
          <span className="hidden sm:inline">Imprimir</span>
        </button>
      )}
    </div>
  );
}

export function ModalDrawer({
  open,
  title,
  subtitle,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: React.ReactNode;
}): React.ReactElement | null {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-900/60 p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div className="w-full sm:max-w-2xl max-h-[92vh] flex flex-col rounded-t-2xl sm:rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden">
        <div className="flex items-start justify-between gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3.5 sm:px-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900">{title}</h2>
            {subtitle && <p className="text-xs sm:text-sm text-slate-600 mt-0.5">{subtitle}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar modal"
            className="min-h-[40px] min-w-[40px] flex items-center justify-center rounded-lg text-slate-600 hover:bg-slate-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="overflow-y-auto p-4 sm:p-6">{children}</div>
      </div>
    </div>
  );
}

export function Field({
  label,
  htmlFor,
  required,
  hint,
  children,
}: {
  label: string;
  htmlFor?: string;
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
}): React.ReactElement {
  return (
    <div className="space-y-1">
      <label htmlFor={htmlFor} className="block text-sm font-semibold text-slate-800">
        {label} {required && <span className="text-red-700" aria-hidden="true">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-slate-600">{hint}</p>}
    </div>
  );
}

export const inputCls =
  "w-full min-h-[44px] rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-red-700 focus:outline-none focus:ring-2 focus:ring-red-700/20 disabled:bg-slate-100";

export function ToastBanner({
  toast,
  onDismiss,
}: {
  toast: { type: "success" | "error" | "warning"; text: string } | null;
  onDismiss: () => void;
}): React.ReactElement | null {
  if (!toast) return null;
  const styles =
    toast.type === "error"
      ? "bg-red-50 border-red-300 text-red-900"
      : toast.type === "warning"
        ? "bg-amber-50 border-amber-300 text-amber-900"
        : "bg-emerald-50 border-emerald-300 text-emerald-900";
  return (
    <div
      role="status"
      className={`mb-4 flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm font-medium ${styles}`}
    >
      <div className="flex items-center gap-2">
        {toast.type === "success" ? (
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-700" />
        ) : (
          <AlertCircle className="h-5 w-5 shrink-0" />
        )}
        <span>{toast.text}</span>
      </div>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Cerrar notificación"
        className="rounded p-1 hover:bg-black/5"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
