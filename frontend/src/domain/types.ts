export type RoleCode = "ADMIN" | "JEFE_PROYECTO" | "OPERARIO" | "CONSULTA";

export type LocalSyncStatus = "synced" | "pending" | "conflict";

export interface BaseEntity {
  id: string;
  version: number;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  _local_sync_status?: LocalSyncStatus;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name: string;
  roles: RoleCode[];
  permissions: string[];
  activo: boolean;
}

export interface OfflineSession {
  key: string;
  user: UserProfile;
  offline_grace_until: string;
  saved_at: string;
}

export interface Variedad extends BaseEntity {
  nombre: string;
  perfil: "CBD" | "THC" | "BALANCEADA";
  descripcion: string;
  activo: boolean;
}

export interface Ubicacion extends BaseEntity {
  nombre: string;
  tipo: "CASA_MALLA" | "INVERNADERO" | "TERRENO" | "SECADO" | "OTRO";
  capacidad_area: number | null;
  activo: boolean;
}

export interface TipoComplicacion extends BaseEntity {
  nombre: string;
  categoria: string;
  activo: boolean;
}

export interface Propagacion extends BaseEntity {
  codigo_lote: string;
  fecha_siembra: string;
  tipo_propagacion: "ESQUEJE" | "SEMILLA" | "IN_VITRO";
  variedad_id: string;
  tipo_incorporacion: "PROPIA" | "COMPRADA";
  cantidad_material: number;
  cantidad_plantas_madre: number;
  lote_origen_id: string | null;
  observaciones: string;
  estado: string;
}

export interface Transplante extends BaseEntity {
  lote_id: string;
  etapa: "BOLSA" | "CAMPO";
  tipo_lote: "PLANTA_MADRE" | "PLANTA_COMERCIAL";
  fecha_transplante: string;
  ubicacion_id: string;
  cama: string;
  surco_inicial: string;
  surco_final: string;
  cantidad_area: number;
  cantidad_buenas: number;
  cantidad_malas: number;
  porcentaje_buenas: number;
  porcentaje_malas: number;
  estado_transplante: "TRANSPLANTE" | "FINALIZADO";
  observaciones: string;
}

export interface PlantaMadre extends BaseEntity {
  lote_id: string;
  numero_planta: string;
  fecha_siembra: string;
  ubicacion_id: string | null;
  lugar_siembra: string;
  observaciones: string;
  estado: string;
}

export interface ExtraccionMaterial extends BaseEntity {
  lote_id: string;
  planta_madre_id: string | null;
  numero_planta_madre: string;
  fecha_extraccion: string;
  fase: string;
  cantidad_esquejes: number;
  cantidad_semillas: number;
  observaciones: string;
}

export interface ControlFase extends BaseEntity {
  lote_id: string;
  transplante_id: string | null;
  numero_planta_campo: string;
  fase_cultivo: string;
  fecha_inicio: string;
  fecha_fin: string | null;
  fecha_descarte: string | null;
  tipo_complicacion_id: string | null;
  tratamiento_aplicado: string;
  estado_revision: "BUENA" | "MALA" | "EN_TRATAMIENTO" | "DESCARTADA";
  observaciones: string;
}

export interface Cosecha extends BaseEntity {
  lote_id: string;
  transplante_campo_id: string | null;
  fecha_suelo: string;
  fecha_cosecha: string;
  numero_plantas: number;
  cama: string;
  estado_cosecha: "PENDIENTE" | "EN_PROCESO" | "FINALIZADA";
  dias_floracion: number;
  peso_verde: number;
  observaciones: string;
}

export interface PostCosecha extends BaseEntity {
  cosecha_id: string;
  lote_id: string;
  fecha_ini_secado: string;
  fecha_fin_secado: string | null;
  peso_flor_verde: number;
  peso_biomasa: number;
  peso_flor_seco: number;
  porcentaje_cbd: number;
  porcentaje_thc: number;
  observaciones: string;
}

export interface Baja extends BaseEntity {
  lote_id: string;
  fecha_baja: string;
  cantidad: number;
  fase_cultivo: string;
  tipo_complicacion_id: string | null;
  observaciones: string;
}

export type SyncEntityType =
  | "variedad"
  | "ubicacion"
  | "tipo_complicacion"
  | "propagacion"
  | "transplante"
  | "planta_madre"
  | "extraccion_material"
  | "control_fase"
  | "cosecha"
  | "post_cosecha"
  | "baja";

export interface OutboxMutation {
  sequence?: number;
  client_mutation_id: string;
  entity_type: SyncEntityType;
  entity_id: string;
  operation: "CREATE" | "UPDATE" | "DELETE";
  base_version: number;
  payload: Record<string, unknown>;
  status: "queued" | "syncing" | "conflict" | "failed";
  attempts: number;
  next_retry_at: number;
  last_error: string | null;
  server_record: Record<string, unknown> | null;
  created_at: string;
}

export interface SyncMeta {
  key: string;
  last_pull_cursor: string | null;
  last_sync_at: string | null;
  client_device_id: string;
}
