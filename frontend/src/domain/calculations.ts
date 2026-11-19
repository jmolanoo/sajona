import type { Baja, Propagacion } from "./types";

export interface SupervivenciaCalculada {
  disponible: number;
  buenas: number;
  malas: number;
  porcentajeBuenas: number;
  porcentajeMalas: number;
  alertaMerma: boolean;
}

export function calcularSaldoVivoLote(lote: Propagacion, bajas: Baja[]): number {
  const totalBajas = bajas
    .filter((b) => b.lote_id === lote.id && !b.deleted_at)
    .reduce((acc, item) => acc + Number(item.cantidad || 0), 0);
  return Math.max(Number(lote.cantidad_material || 0) - totalBajas, 0);
}

export function calcularSupervivencia(
  disponible: number,
  buenas: number
): SupervivenciaCalculada {
  if (disponible <= 0) {
    throw new Error("La cantidad disponible del lote debe ser mayor a cero.");
  }
  if (buenas < 0 || buenas > disponible) {
    throw new Error(`Las unidades buenas deben estar entre 0 y ${disponible}.`);
  }
  const malas = disponible - buenas;
  const porcentajeBuenas = Math.round(((buenas * 100) / disponible) * 100) / 100;
  const porcentajeMalas = Math.round((100 - porcentajeBuenas) * 100) / 100;
  return {
    disponible,
    buenas,
    malas,
    porcentajeBuenas,
    porcentajeMalas,
    alertaMerma: porcentajeMalas > 20,
  };
}

export function calcularDiasFloracion(fechaSuelo: string, fechaCosecha: string): number {
  if (!fechaSuelo || !fechaCosecha) return 0;
  const start = new Date(`${fechaSuelo}T00:00:00Z`).getTime();
  const end = new Date(`${fechaCosecha}T00:00:00Z`).getTime();
  if (end < start) {
    throw new Error("La fecha de cosecha no puede ser anterior al trasplante en campo.");
  }
  return Math.round((end - start) / 86400000);
}

export function calcularRendimientoSecado(pesoVerde: number, pesoSeco: number): number {
  if (pesoVerde <= 0 || pesoSeco < 0) return 0;
  return Math.round(((pesoSeco * 100) / pesoVerde) * 100) / 100;
}

export function generarUuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
