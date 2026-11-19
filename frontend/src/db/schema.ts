import Dexie, { type Table } from "dexie";
import type {
  Baja,
  ControlFase,
  Cosecha,
  ExtraccionMaterial,
  OfflineSession,
  OutboxMutation,
  PlantaMadre,
  PostCosecha,
  Propagacion,
  SyncEntityType,
  SyncMeta,
  TipoComplicacion,
  Transplante,
  Ubicacion,
  Variedad,
} from "../domain/types";

export class SajonaDatabase extends Dexie {
  variedades!: Table<Variedad, string>;
  ubicaciones!: Table<Ubicacion, string>;
  tipos_complicacion!: Table<TipoComplicacion, string>;
  propagaciones!: Table<Propagacion, string>;
  transplantes!: Table<Transplante, string>;
  plantas_madre!: Table<PlantaMadre, string>;
  extracciones_material!: Table<ExtraccionMaterial, string>;
  controles_fase!: Table<ControlFase, string>;
  cosechas!: Table<Cosecha, string>;
  post_cosechas!: Table<PostCosecha, string>;
  bajas!: Table<Baja, string>;
  outbox_mutations!: Table<OutboxMutation, number>;
  sync_meta!: Table<SyncMeta, string>;
  offline_session!: Table<OfflineSession, string>;

  constructor(name = "sajona_offline_db") {
    super(name);
    this.version(1).stores({
      variedades: "id, nombre, updated_at, deleted_at",
      ubicaciones: "id, nombre, tipo, updated_at, deleted_at",
      tipos_complicacion: "id, nombre, updated_at, deleted_at",
      propagaciones: "id, codigo_lote, fecha_siembra, estado, updated_at, deleted_at",
      transplantes: "id, lote_id, etapa, fecha_transplante, updated_at, deleted_at",
      plantas_madre: "id, lote_id, numero_planta, updated_at, deleted_at",
      extracciones_material: "id, lote_id, planta_madre_id, fecha_extraccion, updated_at, deleted_at",
      controles_fase: "id, lote_id, fecha_inicio, estado_revision, updated_at, deleted_at",
      cosechas: "id, lote_id, fecha_cosecha, updated_at, deleted_at",
      post_cosechas: "id, cosecha_id, lote_id, fecha_ini_secado, updated_at, deleted_at",
      bajas: "id, lote_id, fecha_baja, updated_at, deleted_at",
      outbox_mutations: "++sequence, client_mutation_id, entity_type, entity_id, status, next_retry_at",
      sync_meta: "key",
      offline_session: "key",
    });
  }
}

export const db = new SajonaDatabase();

export function tableForEntity(
  database: SajonaDatabase,
  entityType: SyncEntityType
): Table<Record<string, unknown>, string> {
  const map: Record<SyncEntityType, Table<unknown, string>> = {
    variedad: database.variedades,
    ubicacion: database.ubicaciones,
    tipo_complicacion: database.tipos_complicacion,
    propagacion: database.propagaciones,
    transplante: database.transplantes,
    planta_madre: database.plantas_madre,
    extraccion_material: database.extracciones_material,
    control_fase: database.controles_fase,
    cosecha: database.cosechas,
    post_cosecha: database.post_cosechas,
    baja: database.bajas,
  };
  return map[entityType] as Table<Record<string, unknown>, string>;
}
