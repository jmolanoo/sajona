"""Entidades de dominio y metadatos de trazabilidad/sincronización."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

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


def utc_now() -> datetime:
    """Retorna marca temporal UTC con zona horaria."""
    return datetime.now(UTC)


@dataclass
class SyncMetadata:
    """Metadatos transversales de concurrencia optimista y borrado lógico."""

    id: UUID = field(default_factory=uuid4)
    version: int = 1
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    deleted_at: datetime | None = None


@dataclass
class UserIdentity:
    """Identidad autenticada en memoria de aplicación."""

    id: UUID
    username: str
    email: str
    full_name: str
    roles: list[RoleCode]
    permissions: list[str]
    activo: bool


@dataclass
class CatalogoVariedad(SyncMetadata):
    """Variedad de cannabis medicinal registrada."""

    nombre: str = ""
    perfil: PerfilVariedad = PerfilVariedad.CBD
    descripcion: str = ""
    activo: bool = True


@dataclass
class CatalogoUbicacion(SyncMetadata):
    """Ubicación física productiva (Casa Malla, Terreno, Secado)."""

    nombre: str = ""
    tipo: TipoUbicacion = TipoUbicacion.CASA_MALLA
    capacidad_area: Decimal | None = None
    activo: bool = True


@dataclass
class CatalogoComplicacion(SyncMetadata):
    """Tipo de complicación fitosanitaria o operativa."""

    nombre: str = ""
    categoria: str = "FITOSANITARIA"
    activo: bool = True


@dataclass
class PropagacionLote(SyncMetadata):
    """Entidad raíz del ciclo productivo trazable por código de lote."""

    codigo_lote: str = ""
    fecha_siembra: date = field(default_factory=date.today)
    tipo_propagacion: TipoPropagacion = TipoPropagacion.ESQUEJE
    variedad_id: UUID = field(default_factory=uuid4)
    tipo_incorporacion: TipoIncorporacion = TipoIncorporacion.PROPIA
    cantidad_material: int = 0
    cantidad_plantas_madre: int = 0
    lote_origen_id: UUID | None = None
    observaciones: str = ""
    estado: EstadoLote = EstadoLote.PROPAGACION
    created_by: UUID | None = None


@dataclass
class TransplanteRegistro(SyncMetadata):
    """Registro de trasplante a bolsa o trasplante a campo."""

    lote_id: UUID = field(default_factory=uuid4)
    etapa: EtapaTransplante = EtapaTransplante.BOLSA
    tipo_lote: TipoLoteTransplante = TipoLoteTransplante.PLANTA_COMERCIAL
    fecha_transplante: date = field(default_factory=date.today)
    ubicacion_id: UUID = field(default_factory=uuid4)
    cama: str = ""
    surco_inicial: str = ""
    surco_final: str = ""
    cantidad_area: Decimal = Decimal("0.00")
    cantidad_buenas: int = 0
    cantidad_malas: int = 0
    porcentaje_buenas: Decimal = Decimal("100.00")
    porcentaje_malas: Decimal = Decimal("0.00")
    estado_transplante: EstadoTransplante = EstadoTransplante.TRANSPLANTE
    observaciones: str = ""
    created_by: UUID | None = None


@dataclass
class PlantaMadreRegistro(SyncMetadata):
    """Planta madre individual adscrita a un lote."""

    lote_id: UUID = field(default_factory=uuid4)
    numero_planta: str = ""
    fecha_siembra: date = field(default_factory=date.today)
    ubicacion_id: UUID | None = None
    lugar_siembra: str = ""
    observaciones: str = ""
    estado: str = "ACTIVA"
    created_by: UUID | None = None


@dataclass
class ExtraccionMaterialRegistro(SyncMetadata):
    """Extracción de esquejes o semillas desde una planta madre del lote."""

    lote_id: UUID = field(default_factory=uuid4)
    planta_madre_id: UUID | None = None
    numero_planta_madre: str = ""
    fecha_extraccion: date = field(default_factory=date.today)
    fase: FaseCultivo = FaseCultivo.ENRAIZAMIENTO
    cantidad_esquejes: int = 0
    cantidad_semillas: int = 0
    observaciones: str = ""
    created_by: UUID | None = None


@dataclass
class ControlFaseRegistro(SyncMetadata):
    """Control fenológico, revisión periódica e historia clínica en campo/vivero."""

    lote_id: UUID = field(default_factory=uuid4)
    transplante_id: UUID | None = None
    numero_planta_campo: str = ""
    fase_cultivo: FaseCultivo = FaseCultivo.VEGETATIVA
    fecha_inicio: date = field(default_factory=date.today)
    fecha_fin: date | None = None
    fecha_descarte: date | None = None
    tipo_complicacion_id: UUID | None = None
    tratamiento_aplicado: str = ""
    estado_revision: EstadoRevision = EstadoRevision.BUENA
    observaciones: str = ""
    created_by: UUID | None = None


@dataclass
class CosechaRegistro(SyncMetadata):
    """Registro de cosecha de lote en campo."""

    lote_id: UUID = field(default_factory=uuid4)
    transplante_campo_id: UUID | None = None
    fecha_suelo: date = field(default_factory=date.today)
    fecha_cosecha: date = field(default_factory=date.today)
    numero_plantas: int = 0
    cama: str = ""
    estado_cosecha: EstadoCosecha = EstadoCosecha.EN_PROCESO
    dias_floracion: int = 0
    peso_verde: Decimal = Decimal("0.00")
    observaciones: str = ""
    created_by: UUID | None = None


@dataclass
class PostCosechaRegistro(SyncMetadata):
    """Registro de secado, biomasa y análisis de cannabinoides."""

    cosecha_id: UUID = field(default_factory=uuid4)
    lote_id: UUID = field(default_factory=uuid4)
    fecha_ini_secado: date = field(default_factory=date.today)
    fecha_fin_secado: date | None = None
    peso_flor_verde: Decimal = Decimal("0.00")
    peso_biomasa: Decimal = Decimal("0.00")
    peso_flor_seco: Decimal = Decimal("0.00")
    porcentaje_cbd: Decimal = Decimal("0.00")
    porcentaje_thc: Decimal = Decimal("0.00")
    observaciones: str = ""
    created_by: UUID | None = None


@dataclass
class BajaRegistro(SyncMetadata):
    """Registro de descartes o mortalidad de plantas por fase."""

    lote_id: UUID = field(default_factory=uuid4)
    fecha_baja: date = field(default_factory=date.today)
    cantidad: int = 0
    fase_cultivo: FaseCultivo = FaseCultivo.PROPAGACION
    tipo_complicacion_id: UUID | None = None
    observaciones: str = ""
    created_by: UUID | None = None
