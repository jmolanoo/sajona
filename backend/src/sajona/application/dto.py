"""Esquemas Pydantic v2 (DTOs) de entrada/salida y contratos OpenAPI."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field

from sajona.domain.enums import (
    EstadoCosecha,
    EstadoLote,
    EstadoRevision,
    EstadoTransplante,
    EtapaTransplante,
    FaseCultivo,
    PerfilVariedad,
    RoleCode,
    TipoIncorporacion,
    TipoLoteTransplante,
    TipoPropagacion,
    TipoUbicacion,
)


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=4, max_length=128)


class UserProfileDTO(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str
    roles: list[RoleCode]
    permissions: list[str]
    activo: bool


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    offline_grace_until: datetime
    user: UserProfileDTO


class PasswordResetRequestDTO(BaseModel):
    identifier: str = Field(..., min_length=3, max_length=255)


class PasswordResetConfirmDTO(BaseModel):
    token: str = Field(..., min_length=16, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=128)


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    nombres: str = Field(..., min_length=2, max_length=80)
    apellidos: str = Field(..., min_length=2, max_length=80)
    numero_identificacion: str = Field(..., min_length=4, max_length=40)
    telefono: str = Field(..., min_length=6, max_length=30)
    roles: list[RoleCode] = Field(..., min_length=1)


class UpdateUserRequest(BaseModel):
    activo: bool | None = None
    roles: list[RoleCode] | None = None


class VariedadPayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    nombre: str = Field(..., min_length=2, max_length=100)
    perfil: PerfilVariedad = PerfilVariedad.CBD
    descripcion: str = Field(default="", max_length=255)
    activo: bool = True
    version: int = 1


class UbicacionPayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    nombre: str = Field(..., min_length=2, max_length=100)
    tipo: TipoUbicacion = TipoUbicacion.CASA_MALLA
    capacidad_area: Decimal | None = Field(default=None, ge=0)
    activo: bool = True
    version: int = 1


class ComplicacionPayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    nombre: str = Field(..., min_length=2, max_length=100)
    categoria: str = Field(default="FITOSANITARIA", max_length=40)
    activo: bool = True
    version: int = 1


class PropagacionPayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    codigo_lote: str = Field(..., min_length=1, max_length=40)
    fecha_siembra: date
    tipo_propagacion: TipoPropagacion
    variedad_id: UUID
    tipo_incorporacion: TipoIncorporacion
    cantidad_material: int = Field(..., gt=0)
    cantidad_plantas_madre: int = Field(default=0, ge=0)
    lote_origen_id: UUID | None = None
    observaciones: str = Field(default="", max_length=1000)
    estado: EstadoLote = EstadoLote.PROPAGACION
    version: int = 1


class TransplantePayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lote_id: UUID
    etapa: EtapaTransplante
    tipo_lote: TipoLoteTransplante
    fecha_transplante: date
    ubicacion_id: UUID
    cama: str = Field(default="", max_length=50)
    surco_inicial: str = Field(default="", max_length=30)
    surco_final: str = Field(default="", max_length=30)
    cantidad_area: Decimal = Field(default=Decimal("0.00"), ge=0)
    cantidad_buenas: int = Field(..., ge=0)
    estado_transplante: EstadoTransplante = EstadoTransplante.TRANSPLANTE
    observaciones: str = Field(default="", max_length=1000)
    version: int = 1


class PlantaMadrePayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lote_id: UUID
    numero_planta: str = Field(..., min_length=1, max_length=40)
    fecha_siembra: date
    ubicacion_id: UUID | None = None
    lugar_siembra: str = Field(default="", max_length=120)
    observaciones: str = Field(default="", max_length=1000)
    estado: str = Field(default="ACTIVA", max_length=20)
    version: int = 1


class ExtraccionMaterialPayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lote_id: UUID
    planta_madre_id: UUID | None = None
    numero_planta_madre: str = Field(..., min_length=1, max_length=40)
    fecha_extraccion: date
    fase: FaseCultivo = FaseCultivo.ENRAIZAMIENTO
    cantidad_esquejes: int = Field(default=0, ge=0)
    cantidad_semillas: int = Field(default=0, ge=0)
    observaciones: str = Field(default="", max_length=1000)
    version: int = 1


class ControlFasePayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lote_id: UUID
    transplante_id: UUID | None = None
    numero_planta_campo: str = Field(default="", max_length=40)
    fase_cultivo: FaseCultivo = FaseCultivo.VEGETATIVA
    fecha_inicio: date
    fecha_fin: date | None = None
    fecha_descarte: date | None = None
    tipo_complicacion_id: UUID | None = None
    tratamiento_aplicado: str = Field(default="", max_length=500)
    estado_revision: EstadoRevision = EstadoRevision.BUENA
    observaciones: str = Field(default="", max_length=1000)
    version: int = 1


class CosechaPayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lote_id: UUID
    transplante_campo_id: UUID | None = None
    fecha_suelo: date
    fecha_cosecha: date
    numero_plantas: int = Field(..., gt=0)
    cama: str = Field(default="", max_length=50)
    estado_cosecha: EstadoCosecha = EstadoCosecha.EN_PROCESO
    dias_floracion: int | None = Field(default=None, ge=0)
    peso_verde: Decimal = Field(..., gt=0)
    observaciones: str = Field(default="", max_length=1000)
    version: int = 1


class PostCosechaPayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    cosecha_id: UUID
    lote_id: UUID
    fecha_ini_secado: date
    fecha_fin_secado: date | None = None
    peso_flor_verde: Decimal = Field(..., gt=0)
    peso_biomasa: Decimal = Field(default=Decimal("0.00"), ge=0)
    peso_flor_seco: Decimal = Field(default=Decimal("0.00"), ge=0)
    porcentaje_cbd: Decimal = Field(..., ge=0, le=100)
    porcentaje_thc: Decimal = Field(..., ge=0, le=100)
    observaciones: str = Field(default="", max_length=1000)
    version: int = 1


class BajaPayload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lote_id: UUID
    fecha_baja: date
    cantidad: int = Field(..., gt=0)
    fase_cultivo: FaseCultivo
    tipo_complicacion_id: UUID | None = None
    observaciones: str = Field(default="", max_length=1000)
    version: int = 1


class SyncMutationItem(BaseModel):
    client_mutation_id: UUID
    entity_type: str
    entity_id: UUID
    operation: str = Field(..., pattern="^(CREATE|UPDATE|DELETE)$")
    base_version: int = Field(default=0, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncPushRequest(BaseModel):
    client_device_id: str = Field(default="web-pwa", max_length=80)
    mutations: list[SyncMutationItem] = Field(..., max_length=200)


class SyncMutationOutcome(BaseModel):
    client_mutation_id: UUID
    entity_type: str
    entity_id: UUID
    status: str  # applied | duplicate | conflict | rejected
    new_version: int | None = None
    server_record: dict[str, Any] | None = None
    error_code: str | None = None
    message: str | None = None


class SyncPushResponse(BaseModel):
    server_time: datetime
    results: list[SyncMutationOutcome]


class SyncPullResponse(BaseModel):
    server_cursor: datetime
    changes: dict[str, list[dict[str, Any]]]
