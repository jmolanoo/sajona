import React, { useMemo, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { LotTraceModal } from "../components/LotTraceModal";
import { ResponsiveRecordsView, type ColumnDef } from "../components/ResponsiveRecordsView";
import { Field, ModalDrawer, inputCls } from "../components/UiPrimitives";
import { deleteEntityOfflineFirst, saveEntityOfflineFirst, useEntityList } from "../db/useLocalData";
import { calcularSaldoVivoLote, calcularSupervivencia } from "../domain/calculations";
import type { Baja, Propagacion, Transplante, Ubicacion } from "../domain/types";

export function TransplantePage({ etapa }: { etapa: "BOLSA" | "CAMPO" }): React.ReactElement {
  const { hasPermission } = useAuth();
  const allTransplantes = useEntityList<Transplante>("transplante").items;
  const lotes = useEntityList<Propagacion>("propagacion").items;
  const ubicaciones = useEntityList<Ubicacion>("ubicacion").items;
  const bajas = useEntityList<Baja>("baja").items;

  const items = useMemo(
    () => allTransplantes.filter((t) => t.etapa === etapa),
    [allTransplantes, etapa]
  );
  const loteById = new Map(lotes.map((l) => [l.id, l]));
  const ubiById = new Map(ubicaciones.map((u) => [u.id, u.nombre]));

  const [modalOpen, setModalOpen] = useState(false);
  const [notifData, setNotifData] = useState<{
    malas: number;
    pctMalas: number;
    pctBuenas: number;
    alerta: boolean;
  } | null>(null);
  const [editing, setEditing] = useState<Transplante | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);

  const [loteId, setLoteId] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [tipoLote, setTipoLote] = useState<"PLANTA_MADRE" | "PLANTA_COMERCIAL">("PLANTA_COMERCIAL");
  const [ubicacionId, setUbicacionId] = useState("");
  const [cama, setCama] = useState("");
  const [surcoIni, setSurcoIni] = useState("");
  const [surcoFin, setSurcoFin] = useState("");
  const [area, setArea] = useState(40);
  const [buenas, setBuenas] = useState(50);
  const [estadoTp, setEstadoTp] = useState<"TRANSPLANTE" | "FINALIZADO">("FINALIZADO");
  const [obs, setObs] = useState("");

  const selectedLote = loteById.get(loteId);
  const disponible = selectedLote ? calcularSaldoVivoLote(selectedLote, bajas) : 0;

  const previewSurv = useMemo(() => {
    if (!selectedLote || disponible <= 0) return null;
    try {
      return calcularSupervivencia(disponible, Number(buenas));
    } catch {
      return null;
    }
  }, [selectedLote, disponible, buenas]);

  const openNew = (): void => {
    setEditing(null);
    const firstLote = lotes[0];
    setLoteId(firstLote?.id ?? "");
    setFecha(new Date().toISOString().slice(0, 10));
    setTipoLote(etapa === "CAMPO" ? "PLANTA_COMERCIAL" : "PLANTA_MADRE");
    setUbicacionId(ubicaciones[0]?.id ?? "");
    setCama("");
    setSurcoIni("");
    setSurcoFin("");
    setArea(40);
    setBuenas(firstLote ? calcularSaldoVivoLote(firstLote, bajas) : 0);
    setEstadoTp("FINALIZADO");
    setObs("");
    setModalOpen(true);
  };

  const openEdit = (item: Transplante): void => {
    setEditing(item);
    setLoteId(item.lote_id);
    setFecha(item.fecha_transplante);
    setTipoLote(item.tipo_lote);
    setUbicacionId(item.ubicacion_id);
    setCama(item.cama);
    setSurcoIni(item.surco_inicial);
    setSurcoFin(item.surco_final);
    setArea(item.cantidad_area);
    setBuenas(item.cantidad_buenas);
    setEstadoTp(item.estado_transplante);
    setObs(item.observaciones);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    try {
      if (!selectedLote) throw new Error("Seleccione un lote válido.");
      const calc = calcularSupervivencia(disponible, Number(buenas));
      await saveEntityOfflineFirst(
        "transplante",
        {
          lote_id: loteId,
          etapa,
          tipo_lote: etapa === "CAMPO" ? "PLANTA_COMERCIAL" : tipoLote,
          fecha_transplante: fecha,
          ubicacion_id: ubicacionId,
          cama: cama.trim(),
          surco_inicial: surcoIni.trim(),
          surco_final: surcoFin.trim(),
          cantidad_area: Number(area),
          cantidad_buenas: calc.buenas,
          cantidad_malas: calc.malas,
          porcentaje_buenas: calc.porcentajeBuenas,
          porcentaje_malas: calc.porcentajeMalas,
          estado_transplante: estadoTp,
          observaciones: obs.trim(),
        },
        editing
      );
      setModalOpen(false);
      setNotifData({
        malas: calc.malas,
        pctMalas: calc.porcentajeMalas,
        pctBuenas: calc.porcentajeBuenas,
        alerta: calc.alertaMerma,
      });
      setToast({ type: "success", text: `Transplante a ${etapa.toLowerCase()} registrado.` });
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error al guardar." });
    }
  };

  const columns: ColumnDef<Transplante>[] = [
    {
      key: "lote",
      header: "Id Lote",
      render: (t) => <span className="font-bold">{loteById.get(t.lote_id)?.codigo_lote ?? "—"}</span>,
      exportValue: (t) => loteById.get(t.lote_id)?.codigo_lote ?? "",
    },
    {
      key: "fecha",
      header: etapa === "BOLSA" ? "Fecha Bolsa" : "Fecha Campo",
      render: (t) => t.fecha_transplante,
      exportValue: (t) => t.fecha_transplante,
    },
    {
      key: "tipo",
      header: etapa === "BOLSA" ? "Tipo Lote" : "Terreno / Cama",
      render: (t) =>
        etapa === "BOLSA"
          ? t.tipo_lote === "PLANTA_MADRE"
            ? "Planta Madre"
            : "Planta Comercial"
          : `${ubiById.get(t.ubicacion_id) ?? ""} ${t.cama ? `• ${t.cama}` : ""}`,
      exportValue: (t) =>
        etapa === "BOLSA" ? t.tipo_lote : `${ubiById.get(t.ubicacion_id) ?? ""} ${t.cama}`,
    },
    {
      key: "buenas",
      header: "Buenas (%)",
      render: (t) => `${t.cantidad_buenas} (${t.porcentaje_buenas}%)`,
      exportValue: (t) => `${t.cantidad_buenas} (${t.porcentaje_buenas}%)`,
    },
    {
      key: "malas",
      header: "Malas (%)",
      render: (t) => `${t.cantidad_malas} (${t.porcentaje_malas}%)`,
      exportValue: (t) => `${t.cantidad_malas} (${t.porcentaje_malas}%)`,
    },
    {
      key: "estado",
      header: "Estado",
      render: (t) => t.estado_transplante,
      exportValue: (t) => t.estado_transplante,
    },
  ];

  return (
    <>
      <ResponsiveRecordsView
        title={etapa === "BOLSA" ? "Transplante a Bolsa" : "Transplante a Campo"}
        subtitle={
          etapa === "BOLSA"
            ? "Clasificación de lotes a Planta Madre o Comercial con cálculo automático de pérdidas."
            : "Siembra definitiva en terreno comercial por cama y rango de surcos."
        }
        items={items}
        columns={columns}
        dateAccessor={(t) => t.fecha_transplante}
        searchAccessor={(t) =>
          `${loteById.get(t.lote_id)?.codigo_lote ?? ""} ${ubiById.get(t.ubicacion_id) ?? ""} ${t.cama} ${t.tipo_lote}`
        }
        loteIdAccessor={(t) => t.lote_id}
        canWrite={hasPermission("production:write")}
        canDelete={hasPermission("production:delete")}
        onNew={openNew}
        onEdit={openEdit}
        onDelete={(t) => void deleteEntityOfflineFirst("transplante", t)}
        onTraceLot={(id) => setTraceId(id)}
        toast={toast}
        onDismissToast={() => setToast(null)}
      />

      <ModalDrawer
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={
          editing
            ? `Editar Transplante ${etapa}`
            : etapa === "BOLSA"
              ? "Nuevo Transplante a Bolsa"
              : "Nuevo Transplante a Campo"
        }
      >
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Id Lote" htmlFor="tp-lote" required>
              <select
                id="tp-lote"
                required
                value={loteId}
                onChange={(e) => setLoteId(e.target.value)}
                className={inputCls}
              >
                <option value="">Seleccione...</option>
                {lotes.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.codigo_lote} (Saldo vivo: {calcularSaldoVivoLote(l, bajas)})
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Fecha Transplante" htmlFor="tp-fecha" required>
              <input
                id="tp-fecha"
                type="date"
                required
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                className={inputCls}
              />
            </Field>
            {etapa === "BOLSA" && (
              <Field label="Tipo de Lote" htmlFor="tp-tipolote" required>
                <select
                  id="tp-tipolote"
                  value={tipoLote}
                  onChange={(e) =>
                    setTipoLote(e.target.value as "PLANTA_MADRE" | "PLANTA_COMERCIAL")
                  }
                  className={inputCls}
                >
                  <option value="PLANTA_MADRE">Planta Madre</option>
                  <option value="PLANTA_COMERCIAL">Planta Comercial</option>
                </select>
              </Field>
            )}
            <Field label={etapa === "BOLSA" ? "Ubicación (Casa malla)" : "Terreno"} htmlFor="tp-ubi" required>
              <select
                id="tp-ubi"
                required
                value={ubicacionId}
                onChange={(e) => setUbicacionId(e.target.value)}
                className={inputCls}
              >
                <option value="">Seleccione...</option>
                {ubicaciones.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre} ({u.tipo})
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Cantidad Buenas" htmlFor="tp-buenas" required hint={`Saldo disponible del lote: ${disponible}`}>
              <input
                id="tp-buenas"
                type="number"
                min={0}
                max={Math.max(disponible, 0)}
                required
                value={buenas}
                onChange={(e) => setBuenas(Number(e.target.value))}
                className={inputCls}
              />
            </Field>
            <Field label="Área (m²)" htmlFor="tp-area">
              <input
                id="tp-area"
                type="number"
                min={0}
                step="0.01"
                value={area}
                onChange={(e) => setArea(Number(e.target.value))}
                className={inputCls}
              />
            </Field>
            <Field label="Cama" htmlFor="tp-cama">
              <input
                id="tp-cama"
                value={cama}
                onChange={(e) => setCama(e.target.value)}
                placeholder="ej. Cama 2"
                className={inputCls}
              />
            </Field>
            {etapa === "CAMPO" && (
              <>
                <Field label="Surco Inicial" htmlFor="tp-sini">
                  <input
                    id="tp-sini"
                    value={surcoIni}
                    onChange={(e) => setSurcoIni(e.target.value)}
                    placeholder="ej. S-01"
                    className={inputCls}
                  />
                </Field>
                <Field label="Surco Final" htmlFor="tp-sfin">
                  <input
                    id="tp-sfin"
                    value={surcoFin}
                    onChange={(e) => setSurcoFin(e.target.value)}
                    placeholder="ej. S-06"
                    className={inputCls}
                  />
                </Field>
              </>
            )}
            <Field label="Estado" htmlFor="tp-estado">
              <select
                id="tp-estado"
                value={estadoTp}
                onChange={(e) => setEstadoTp(e.target.value as "TRANSPLANTE" | "FINALIZADO")}
                className={inputCls}
              >
                <option value="TRANSPLANTE">Transplante</option>
                <option value="FINALIZADO">Finalizado</option>
              </select>
            </Field>
          </div>

          {previewSurv && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 grid grid-cols-3 gap-2 text-center text-xs">
              <div>
                <span className="text-slate-600">Malas</span>
                <p className="font-extrabold text-red-800 text-base">{previewSurv.malas}</p>
              </div>
              <div>
                <span className="text-slate-600">% Malas</span>
                <p className="font-extrabold text-red-800 text-base">{previewSurv.porcentajeMalas}%</p>
              </div>
              <div>
                <span className="text-slate-600">% Buenas</span>
                <p className="font-extrabold text-emerald-800 text-base">{previewSurv.porcentajeBuenas}%</p>
              </div>
            </div>
          )}

          <Field label="Observaciones" htmlFor="tp-obs">
            <textarea
              id="tp-obs"
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
              className="min-h-[44px] rounded-xl bg-emerald-700 px-5 text-sm font-bold text-white hover:bg-emerald-800"
            >
              Guardar
            </button>
          </div>
        </form>
      </ModalDrawer>

      {/* Modal de Notificación de Supervivencia (Mockups pág. 8) */}
      <ModalDrawer
        open={Boolean(notifData)}
        onClose={() => setNotifData(null)}
        title="Notificación de Transplante"
        subtitle="Cálculo automático de supervivencia y merma del lote."
      >
        {notifData && (
          <div className="space-y-4">
            {notifData.alerta && (
              <div className="flex items-center gap-2 rounded-xl border border-amber-300 bg-amber-50 p-3 text-xs font-semibold text-amber-900">
                <AlertTriangle className="h-5 w-5 shrink-0 text-amber-700" />
                <span>Alerta fitosanitaria: la pérdida supera el umbral del 20%.</span>
              </div>
            )}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between border-b py-2">
                <span className="font-semibold text-slate-700">Cantidad Malas:</span>
                <span className="font-extrabold text-red-800">{notifData.malas}</span>
              </div>
              <div className="flex justify-between border-b py-2">
                <span className="font-semibold text-slate-700">Porcentaje Malas:</span>
                <span className="font-extrabold text-red-800">{notifData.pctMalas}%</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="font-semibold text-slate-700">Porcentaje Buenas:</span>
                <span className="font-extrabold text-emerald-800">{notifData.pctBuenas}%</span>
              </div>
            </div>
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setNotifData(null)}
                className="min-h-[44px] rounded-xl bg-emerald-700 px-6 text-sm font-bold text-white"
              >
                OK
              </button>
            </div>
          </div>
        )}
      </ModalDrawer>

      <LotTraceModal loteId={traceId} onClose={() => setTraceId(null)} />
    </>
  );
}
