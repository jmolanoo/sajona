"""Fábrica uniforme y serialización de entidades productivas y catálogos."""

from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from sajona.application.dto import (
    BajaPayload,
    ComplicacionPayload,
    ControlFasePayload,
    CosechaPayload,
    ExtraccionMaterialPayload,
    PlantaMadrePayload,
    PostCosechaPayload,
    PropagacionPayload,
    TransplantePayload,
    UbicacionPayload,
    VariedadPayload,
)
from sajona.application.ports import ProduccionPort
from sajona.domain.entities import (
    BajaRegistro,
    CatalogoComplicacion,
    CatalogoUbicacion,
    CatalogoVariedad,
    ControlFaseRegistro,
    CosechaRegistro,
    ExtraccionMaterialRegistro,
    PlantaMadreRegistro,
    PostCosechaRegistro,
    PropagacionLote,
    TransplanteRegistro,
    utc_now,
)
from sajona.domain.exceptions import NotFoundError, ValidationError
from sajona.domain.rules import (
    calcular_dias_floracion,
    calcular_resumen_secado,
    calcular_supervivencia_transplante,
    validar_baja_contra_saldo,
    validar_porcentaje_cannabinoide,
    validar_rango_fechas_fase,
)

PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    "variedad": VariedadPayload,
    "ubicacion": UbicacionPayload,
    "tipo_complicacion": ComplicacionPayload,
    "propagacion": PropagacionPayload,
    "transplante": TransplantePayload,
    "planta_madre": PlantaMadrePayload,
    "extraccion_material": ExtraccionMaterialPayload,
    "control_fase": ControlFasePayload,
    "cosecha": CosechaPayload,
    "post_cosecha": PostCosechaPayload,
    "baja": BajaPayload,
}


def serialize_entity(entity: Any) -> dict[str, Any]:
    """Convierte cualquier dataclass de dominio a diccionario JSON-compatible."""
    raw = asdict(entity)
    out: dict[str, Any] = {}
    for key, val in raw.items():
        if isinstance(val, UUID):
            out[key] = str(val)
        elif isinstance(val, datetime | date):
            out[key] = val.isoformat()
        elif isinstance(val, Decimal):
            out[key] = float(val)
        elif isinstance(val, Enum):
            out[key] = val.value
        else:
            out[key] = val
    return out


async def build_and_validate_entity(
    entity_type: str,
    raw_payload: dict[str, Any],
    repo: ProduccionPort,
    actor_id: UUID,
    existing: Any | None = None,
) -> Any:
    """Valida DTO + reglas de negocio de dominio y construye la entidad lista para persistir."""
    model_cls = PAYLOAD_MODELS.get(entity_type)
    if not model_cls:
        raise ValidationError(f"Tipo de entidad no soportado: '{entity_type}'.")

    dto = model_cls.model_validate(raw_payload)
    now = utc_now()
    next_version = (existing.version + 1) if existing else 1
    created_at = existing.created_at if existing else now
    created_by = existing.created_by if (existing and hasattr(existing, "created_by")) else actor_id

    builder = _BUILDERS[entity_type]
    return await builder(dto, repo, next_version, created_at, now, created_by, existing)


async def _build_variedad(
    dto: VariedadPayload,
    _repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    _actor_id: UUID,
    _existing: Any,
) -> CatalogoVariedad:
    return CatalogoVariedad(
        id=dto.id,
        nombre=dto.nombre.strip(),
        perfil=dto.perfil,
        descripcion=dto.descripcion.strip(),
        activo=dto.activo,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_ubicacion(
    dto: UbicacionPayload,
    _repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    _actor_id: UUID,
    _existing: Any,
) -> CatalogoUbicacion:
    return CatalogoUbicacion(
        id=dto.id,
        nombre=dto.nombre.strip(),
        tipo=dto.tipo,
        capacidad_area=dto.capacidad_area,
        activo=dto.activo,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_complicacion(
    dto: ComplicacionPayload,
    _repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    _actor_id: UUID,
    _existing: Any,
) -> CatalogoComplicacion:
    return CatalogoComplicacion(
        id=dto.id,
        nombre=dto.nombre.strip(),
        categoria=dto.categoria.strip(),
        activo=dto.activo,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_propagacion(
    dto: PropagacionPayload,
    repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    created_by: UUID | None,
    existing: Any,
) -> PropagacionLote:
    by_code = await repo.get_lote_by_codigo(dto.codigo_lote.strip())
    if by_code and (not existing or by_code.id != existing.id):
        raise ValidationError(f"El código de lote '{dto.codigo_lote}' ya está registrado.")
    return PropagacionLote(
        id=dto.id,
        codigo_lote=dto.codigo_lote.strip(),
        fecha_siembra=dto.fecha_siembra,
        tipo_propagacion=dto.tipo_propagacion,
        variedad_id=dto.variedad_id,
        tipo_incorporacion=dto.tipo_incorporacion,
        cantidad_material=dto.cantidad_material,
        cantidad_plantas_madre=dto.cantidad_plantas_madre,
        lote_origen_id=dto.lote_origen_id,
        observaciones=dto.observaciones.strip(),
        estado=dto.estado,
        created_by=created_by,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_transplante(
    dto: TransplantePayload,
    repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    created_by: UUID | None,
    _existing: Any,
) -> TransplanteRegistro:
    lote = await repo.get_entity("propagacion", dto.lote_id)
    if not lote or lote.deleted_at is not None:
        raise NotFoundError("Lote de propagación", str(dto.lote_id))
    bajas = await repo.sum_bajas_lote(dto.lote_id)
    disponible = max(lote.cantidad_material - bajas, 0)
    supervivencia = calcular_supervivencia_transplante(disponible, dto.cantidad_buenas)
    return TransplanteRegistro(
        id=dto.id,
        lote_id=dto.lote_id,
        etapa=dto.etapa,
        tipo_lote=dto.tipo_lote,
        fecha_transplante=dto.fecha_transplante,
        ubicacion_id=dto.ubicacion_id,
        cama=dto.cama.strip(),
        surco_inicial=dto.surco_inicial.strip(),
        surco_final=dto.surco_final.strip(),
        cantidad_area=dto.cantidad_area,
        cantidad_buenas=supervivencia.cantidad_buenas,
        cantidad_malas=supervivencia.cantidad_malas,
        porcentaje_buenas=supervivencia.porcentaje_buenas,
        porcentaje_malas=supervivencia.porcentaje_malas,
        estado_transplante=dto.estado_transplante,
        observaciones=dto.observaciones.strip(),
        created_by=created_by,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_planta_madre(
    dto: PlantaMadrePayload,
    repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    created_by: UUID | None,
    _existing: Any,
) -> PlantaMadreRegistro:
    lote = await repo.get_entity("propagacion", dto.lote_id)
    if not lote or lote.deleted_at is not None:
        raise NotFoundError("Lote de propagación", str(dto.lote_id))
    return PlantaMadreRegistro(
        id=dto.id,
        lote_id=dto.lote_id,
        numero_planta=dto.numero_planta.strip(),
        fecha_siembra=dto.fecha_siembra,
        ubicacion_id=dto.ubicacion_id,
        lugar_siembra=dto.lugar_siembra.strip(),
        observaciones=dto.observaciones.strip(),
        estado=dto.estado.strip(),
        created_by=created_by,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_extraccion(
    dto: ExtraccionMaterialPayload,
    repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    created_by: UUID | None,
    _existing: Any,
) -> ExtraccionMaterialRegistro:
    lote = await repo.get_entity("propagacion", dto.lote_id)
    if not lote or lote.deleted_at is not None:
        raise NotFoundError("Lote de propagación", str(dto.lote_id))
    if dto.cantidad_esquejes == 0 and dto.cantidad_semillas == 0:
        raise ValidationError("Debe registrar al menos 1 esqueje o 1 semilla extraída.")
    return ExtraccionMaterialRegistro(
        id=dto.id,
        lote_id=dto.lote_id,
        planta_madre_id=dto.planta_madre_id,
        numero_planta_madre=dto.numero_planta_madre.strip(),
        fecha_extraccion=dto.fecha_extraccion,
        fase=dto.fase,
        cantidad_esquejes=dto.cantidad_esquejes,
        cantidad_semillas=dto.cantidad_semillas,
        observaciones=dto.observaciones.strip(),
        created_by=created_by,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_control_fase(
    dto: ControlFasePayload,
    repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    created_by: UUID | None,
    _existing: Any,
) -> ControlFaseRegistro:
    lote = await repo.get_entity("propagacion", dto.lote_id)
    if not lote or lote.deleted_at is not None:
        raise NotFoundError("Lote de propagación", str(dto.lote_id))
    validar_rango_fechas_fase(dto.fecha_inicio, dto.fecha_fin, dto.fecha_descarte)
    return ControlFaseRegistro(
        id=dto.id,
        lote_id=dto.lote_id,
        transplante_id=dto.transplante_id,
        numero_planta_campo=dto.numero_planta_campo.strip(),
        fase_cultivo=dto.fase_cultivo,
        fecha_inicio=dto.fecha_inicio,
        fecha_fin=dto.fecha_fin,
        fecha_descarte=dto.fecha_descarte,
        tipo_complicacion_id=dto.tipo_complicacion_id,
        tratamiento_aplicado=dto.tratamiento_aplicado.strip(),
        estado_revision=dto.estado_revision,
        observaciones=dto.observaciones.strip(),
        created_by=created_by,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_cosecha(
    dto: CosechaPayload,
    repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    created_by: UUID | None,
    _existing: Any,
) -> CosechaRegistro:
    lote = await repo.get_entity("propagacion", dto.lote_id)
    if not lote or lote.deleted_at is not None:
        raise NotFoundError("Lote de propagación", str(dto.lote_id))
    dias = (
        dto.dias_floracion
        if dto.dias_floracion is not None
        else calcular_dias_floracion(dto.fecha_suelo, dto.fecha_cosecha)
    )
    calcular_dias_floracion(dto.fecha_suelo, dto.fecha_cosecha)
    return CosechaRegistro(
        id=dto.id,
        lote_id=dto.lote_id,
        transplante_campo_id=dto.transplante_campo_id,
        fecha_suelo=dto.fecha_suelo,
        fecha_cosecha=dto.fecha_cosecha,
        numero_plantas=dto.numero_plantas,
        cama=dto.cama.strip(),
        estado_cosecha=dto.estado_cosecha,
        dias_floracion=dias,
        peso_verde=dto.peso_verde,
        observaciones=dto.observaciones.strip(),
        created_by=created_by,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_post_cosecha(
    dto: PostCosechaPayload,
    repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    created_by: UUID | None,
    _existing: Any,
) -> PostCosechaRegistro:
    cosecha = await repo.get_entity("cosecha", dto.cosecha_id)
    if not cosecha or cosecha.deleted_at is not None:
        raise NotFoundError("Cosecha", str(dto.cosecha_id))
    resumen = calcular_resumen_secado(
        dto.peso_flor_verde,
        dto.peso_biomasa,
        dto.peso_flor_seco,
        dto.fecha_ini_secado,
        dto.fecha_fin_secado,
    )
    cbd = validar_porcentaje_cannabinoide("CBD", dto.porcentaje_cbd)
    thc = validar_porcentaje_cannabinoide("THC", dto.porcentaje_thc)
    return PostCosechaRegistro(
        id=dto.id,
        cosecha_id=dto.cosecha_id,
        lote_id=cosecha.lote_id,
        fecha_ini_secado=dto.fecha_ini_secado,
        fecha_fin_secado=dto.fecha_fin_secado,
        peso_flor_verde=resumen.peso_flor_verde,
        peso_biomasa=resumen.peso_biomasa,
        peso_flor_seco=resumen.peso_flor_seco,
        porcentaje_cbd=cbd,
        porcentaje_thc=thc,
        observaciones=dto.observaciones.strip(),
        created_by=created_by,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


async def _build_baja(
    dto: BajaPayload,
    repo: ProduccionPort,
    version: int,
    created_at: datetime,
    updated_at: datetime,
    created_by: UUID | None,
    existing: Any,
) -> BajaRegistro:
    lote = await repo.get_entity("propagacion", dto.lote_id)
    if not lote or lote.deleted_at is not None:
        raise NotFoundError("Lote de propagación", str(dto.lote_id))
    exclude_id = existing.id if existing else None
    bajas_previas = await repo.sum_bajas_lote(dto.lote_id, exclude_baja_id=exclude_id)
    validar_baja_contra_saldo(lote.cantidad_material, bajas_previas, dto.cantidad)
    return BajaRegistro(
        id=dto.id,
        lote_id=dto.lote_id,
        fecha_baja=dto.fecha_baja,
        cantidad=dto.cantidad,
        fase_cultivo=dto.fase_cultivo,
        tipo_complicacion_id=dto.tipo_complicacion_id,
        observaciones=dto.observaciones.strip(),
        created_by=created_by,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )


_BUILDERS: dict[str, Any] = {
    "variedad": _build_variedad,
    "ubicacion": _build_ubicacion,
    "tipo_complicacion": _build_complicacion,
    "propagacion": _build_propagacion,
    "transplante": _build_transplante,
    "planta_madre": _build_planta_madre,
    "extraccion_material": _build_extraccion,
    "control_fase": _build_control_fase,
    "cosecha": _build_cosecha,
    "post_cosecha": _build_post_cosecha,
    "baja": _build_baja,
}
