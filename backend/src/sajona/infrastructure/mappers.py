"""Mapeadores uniformes entre modelos ORM SQLAlchemy y entidades de dominio."""

from dataclasses import fields
from datetime import UTC, datetime
from enum import Enum
from typing import Any

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
)
from sajona.infrastructure.models import (
    BajaModel,
    ControlFaseModel,
    CosechaModel,
    ExtraccionMaterialModel,
    PlantaMadreModel,
    PostCosechaModel,
    PropagacionModel,
    TipoComplicacionModel,
    TransplanteModel,
    UbicacionModel,
    VariedadModel,
)

ENTITY_SPECS: dict[str, tuple[type[Any], type[Any], str | None]] = {
    "variedad": (VariedadModel, CatalogoVariedad, None),
    "ubicacion": (UbicacionModel, CatalogoUbicacion, None),
    "tipo_complicacion": (TipoComplicacionModel, CatalogoComplicacion, None),
    "propagacion": (PropagacionModel, PropagacionLote, "fecha_siembra"),
    "transplante": (TransplanteModel, TransplanteRegistro, "fecha_transplante"),
    "planta_madre": (PlantaMadreModel, PlantaMadreRegistro, "fecha_siembra"),
    "extraccion_material": (
        ExtraccionMaterialModel,
        ExtraccionMaterialRegistro,
        "fecha_extraccion",
    ),
    "control_fase": (ControlFaseModel, ControlFaseRegistro, "fecha_inicio"),
    "cosecha": (CosechaModel, CosechaRegistro, "fecha_cosecha"),
    "post_cosecha": (PostCosechaModel, PostCosechaRegistro, "fecha_ini_secado"),
    "baja": (BajaModel, BajaRegistro, "fecha_baja"),
}


def _ensure_tz(value: Any) -> Any:
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def orm_to_entity(entity_type: str, model_obj: Any) -> Any:
    """Convierte un registro SQLAlchemy en su dataclass de dominio correspondiente."""
    _, entity_cls, _ = ENTITY_SPECS[entity_type]
    kwargs: dict[str, Any] = {}
    for f in fields(entity_cls):
        raw = getattr(model_obj, f.name)
        val = _ensure_tz(raw)
        if isinstance(f.type, type) and issubclass(f.type, Enum) and val is not None:
            val = f.type(val)
        kwargs[f.name] = val
    return entity_cls(**kwargs)


def apply_entity_to_orm(entity_type: str, entity: Any, target: Any | None = None) -> Any:
    """Copia campos de entidad de dominio a una instancia ORM nueva o existente."""
    model_cls, _, _ = ENTITY_SPECS[entity_type]
    obj = target if target is not None else model_cls()
    for f in fields(entity):
        val = getattr(entity, f.name)
        if isinstance(val, Enum):
            val = val.value
        setattr(obj, f.name, val)
    return obj
