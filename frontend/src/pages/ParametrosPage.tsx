import React, { useState } from "react";
import { Plus } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { Field, SyncBadge, ToastBanner, inputCls } from "../components/UiPrimitives";
import { saveEntityOfflineFirst, useEntityList } from "../db/useLocalData";
import type { TipoComplicacion, Ubicacion, Variedad } from "../domain/types";

export function ParametrosPage(): React.ReactElement {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission("catalogs:write");
  const variedades = useEntityList<Variedad>("variedad").items;
  const ubicaciones = useEntityList<Ubicacion>("ubicacion").items;
  const complicaciones = useEntityList<TipoComplicacion>("tipo_complicacion").items;

  const [tab, setTab] = useState<"variedad" | "ubicacion" | "tipo_complicacion">("variedad");
  const [nombre, setNombre] = useState("");
  const [subtipo, setSubtipo] = useState("CBD");
  const [toast, setToast] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);

  const handleCreate = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    try {
      if (tab === "variedad") {
        await saveEntityOfflineFirst("variedad", {
          nombre: nombre.trim(),
          perfil: subtipo,
          descripcion: "Catálogo parametrizado",
          activo: true,
        });
      } else if (tab === "ubicacion") {
        await saveEntityOfflineFirst("ubicacion", {
          nombre: nombre.trim(),
          tipo: subtipo,
          capacidad_area: 100,
          activo: true,
        });
      } else {
        await saveEntityOfflineFirst("tipo_complicacion", {
          nombre: nombre.trim(),
          categoria: subtipo,
          activo: true,
        });
      }
      setNombre("");
      setToast({ type: "success", text: "Parámetro guardado." });
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error al guardar." });
    }
  };

  return (
    <div className="space-y-4">
      <ToastBanner toast={toast} onDismiss={() => setToast(null)} />
      <div>
        <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">Parámetros y Catálogos</h1>
        <p className="text-xs sm:text-sm text-slate-600">
          Variedades, ubicaciones productivas (casas malla, terrenos, secado) y tipos de complicación.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["variedad", "Variedades", "CBD"],
            ["ubicacion", "Ubicaciones / Terrenos", "CASA_MALLA"],
            ["tipo_complicacion", "Complicaciones", "FITOSANITARIA"],
          ] as const
        ).map(([id, label, defSub]) => (
          <button
            key={id}
            type="button"
            onClick={() => {
              setTab(id);
              setSubtipo(defSub);
            }}
            className={`min-h-[40px] rounded-xl px-4 text-sm font-bold border ${
              tab === id
                ? "bg-red-800 text-white border-red-800"
                : "bg-white text-slate-700 border-slate-300"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {canWrite && (
        <form
          onSubmit={(e) => void handleCreate(e)}
          className="rounded-xl border border-slate-200 bg-white p-4 grid grid-cols-1 sm:grid-cols-3 gap-3 items-end"
        >
          <Field label="Nombre" htmlFor="par-nom" required>
            <input
              id="par-nom"
              required
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              className={inputCls}
            />
          </Field>
          <Field label="Clasificación" htmlFor="par-sub">
            <select
              id="par-sub"
              value={subtipo}
              onChange={(e) => setSubtipo(e.target.value)}
              className={inputCls}
            >
              {tab === "variedad" && (
                <>
                  <option value="CBD">CBD</option>
                  <option value="BALANCEADA">Balanceada</option>
                  <option value="THC">THC</option>
                </>
              )}
              {tab === "ubicacion" && (
                <>
                  <option value="CASA_MALLA">Casa Malla</option>
                  <option value="INVERNADERO">Invernadero</option>
                  <option value="TERRENO">Terreno</option>
                  <option value="SECADO">Secado</option>
                </>
              )}
              {tab === "tipo_complicacion" && (
                <>
                  <option value="FITOSANITARIA">Fitosanitaria</option>
                  <option value="PLAGA">Plaga</option>
                  <option value="NUTRICIONAL">Nutricional</option>
                  <option value="AMBIENTAL">Ambiental</option>
                </>
              )}
            </select>
          </Field>
          <button
            type="submit"
            className="min-h-[44px] inline-flex items-center justify-center gap-1.5 rounded-xl bg-emerald-700 px-4 text-sm font-bold text-white"
          >
            <Plus className="h-4 w-4" />
            Agregar
          </button>
        </form>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {tab === "variedad" &&
          variedades.map((v) => (
            <div key={v.id} className="rounded-xl border border-slate-200 bg-white p-3.5 flex justify-between items-center">
              <div>
                <p className="font-bold text-slate-900">{v.nombre}</p>
                <p className="text-xs text-slate-600">Perfil: {v.perfil}</p>
              </div>
              <SyncBadge status={v._local_sync_status} />
            </div>
          ))}
        {tab === "ubicacion" &&
          ubicaciones.map((u) => (
            <div key={u.id} className="rounded-xl border border-slate-200 bg-white p-3.5 flex justify-between items-center">
              <div>
                <p className="font-bold text-slate-900">{u.nombre}</p>
                <p className="text-xs text-slate-600">Tipo: {u.tipo}</p>
              </div>
              <SyncBadge status={u._local_sync_status} />
            </div>
          ))}
        {tab === "tipo_complicacion" &&
          complicaciones.map((c) => (
            <div key={c.id} className="rounded-xl border border-slate-200 bg-white p-3.5 flex justify-between items-center">
              <div>
                <p className="font-bold text-slate-900">{c.nombre}</p>
                <p className="text-xs text-slate-600">Categoría: {c.categoria}</p>
              </div>
              <SyncBadge status={c._local_sync_status} />
            </div>
          ))}
      </div>
    </div>
  );
}
