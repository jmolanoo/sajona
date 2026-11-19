"""Modelos ORM SQLAlchemy 2 con esquema corregido y soporte Offline-First."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

JSONType = JSON().with_variant(JSONB(), "postgresql")  # type: ignore[no-untyped-call]


class Base(DeclarativeBase):
    """Clase base declarativa para SQLAlchemy."""


class SyncMixin:
    """Columnas comunes de auditoría temporal, concurrencia optimista y borrado lógico."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FuncionarioModel(SyncMixin, Base):
    __tablename__ = "funcionarios"

    nombres: Mapped[str] = mapped_column(String(80), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(80), nullable=False)
    numero_identificacion: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    correo: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class UsuarioModel(SyncMixin, Base):
    __tablename__ = "usuarios"

    funcionario_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("funcionarios.id"), unique=True, nullable=True
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_vencimiento: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fecha_cambio_password: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reset_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RolModel(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(120), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PermisoModel(Base):
    __tablename__ = "permisos"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    codigo: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(160), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class UsuarioRolModel(Base):
    __tablename__ = "usuario_roles"

    usuario_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    rol_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )


class PermisoRolModel(Base):
    __tablename__ = "permiso_roles"

    rol_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permiso_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True
    )


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    usuario_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    usuario_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    entidad: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    entidad_id: Mapped[str] = mapped_column(String(64), nullable=False)
    operacion: Mapped[str] = mapped_column(String(30), nullable=False)
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)
    fuente: Mapped[str] = mapped_column(String(30), nullable=False)
    client_mutation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detalle_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )


class ProcessedMutationModel(Base):
    __tablename__ = "processed_mutations"

    client_mutation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    usuario_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    entidad: Mapped[str] = mapped_column(String(60), nullable=False)
    entidad_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    operacion: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class VariedadModel(SyncMixin, Base):
    __tablename__ = "variedades"

    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    perfil: Mapped[str] = mapped_column(String(30), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class UbicacionModel(SyncMixin, Base):
    __tablename__ = "ubicaciones"

    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    capacidad_area: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TipoComplicacionModel(SyncMixin, Base):
    __tablename__ = "tipos_complicacion"

    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    categoria: Mapped[str] = mapped_column(String(40), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PropagacionModel(SyncMixin, Base):
    __tablename__ = "propagaciones"

    codigo_lote: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    fecha_siembra: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    tipo_propagacion: Mapped[str] = mapped_column(String(20), nullable=False)
    variedad_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("variedades.id"), nullable=False
    )
    tipo_incorporacion: Mapped[str] = mapped_column(String(20), nullable=False)
    cantidad_material: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_plantas_madre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lote_origen_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propagaciones.id"), nullable=True
    )
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PROPAGACION")
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)


class TransplanteModel(SyncMixin, Base):
    __tablename__ = "transplantes"

    lote_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propagaciones.id"), nullable=False, index=True
    )
    etapa: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo_lote: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_transplante: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ubicacion_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ubicaciones.id"), nullable=False
    )
    cama: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    surco_inicial: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    surco_final: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    cantidad_area: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    cantidad_buenas: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_malas: Mapped[int] = mapped_column(Integer, nullable=False)
    porcentaje_buenas: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    porcentaje_malas: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    estado_transplante: Mapped[str] = mapped_column(String(20), nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)


class PlantaMadreModel(SyncMixin, Base):
    __tablename__ = "plantas_madre"

    lote_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propagaciones.id"), nullable=False, index=True
    )
    numero_planta: Mapped[str] = mapped_column(String(40), nullable=False)
    fecha_siembra: Mapped[date] = mapped_column(Date, nullable=False)
    ubicacion_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ubicaciones.id"), nullable=True
    )
    lugar_siembra: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVA")
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)


class ExtraccionMaterialModel(SyncMixin, Base):
    __tablename__ = "extracciones_material"

    lote_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propagaciones.id"), nullable=False, index=True
    )
    planta_madre_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("plantas_madre.id"), nullable=True
    )
    numero_planta_madre: Mapped[str] = mapped_column(String(40), nullable=False)
    fecha_extraccion: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fase: Mapped[str] = mapped_column(String(30), nullable=False)
    cantidad_esquejes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_semillas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)


class ControlFaseModel(SyncMixin, Base):
    __tablename__ = "controles_fase"

    lote_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propagaciones.id"), nullable=False, index=True
    )
    transplante_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("transplantes.id"), nullable=True
    )
    numero_planta_campo: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    fase_cultivo: Mapped[str] = mapped_column(String(30), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_descarte: Mapped[date | None] = mapped_column(Date, nullable=True)
    tipo_complicacion_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tipos_complicacion.id"), nullable=True
    )
    tratamiento_aplicado: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estado_revision: Mapped[str] = mapped_column(String(20), nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)


class CosechaModel(SyncMixin, Base):
    __tablename__ = "cosechas"

    lote_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propagaciones.id"), nullable=False, index=True
    )
    transplante_campo_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("transplantes.id"), nullable=True
    )
    fecha_suelo: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_cosecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    numero_plantas: Mapped[int] = mapped_column(Integer, nullable=False)
    cama: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    estado_cosecha: Mapped[str] = mapped_column(String(30), nullable=False)
    dias_floracion: Mapped[int] = mapped_column(Integer, nullable=False)
    peso_verde: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)


class PostCosechaModel(SyncMixin, Base):
    __tablename__ = "post_cosechas"

    cosecha_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cosechas.id"), nullable=False, index=True
    )
    lote_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propagaciones.id"), nullable=False, index=True
    )
    fecha_ini_secado: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fecha_fin_secado: Mapped[date | None] = mapped_column(Date, nullable=True)
    peso_flor_verde: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    peso_biomasa: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    peso_flor_seco: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    porcentaje_cbd: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    porcentaje_thc: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)


class BajaModel(SyncMixin, Base):
    __tablename__ = "bajas"

    lote_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propagaciones.id"), nullable=False, index=True
    )
    fecha_baja: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    fase_cultivo: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo_complicacion_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tipos_complicacion.id"), nullable=True
    )
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
