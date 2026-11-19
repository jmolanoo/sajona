"""Puertos (interfaces) de infraestructura requeridos por la capa de aplicación."""

from datetime import date, datetime
from typing import Any, Protocol
from uuid import UUID

from sajona.domain.entities import (
    CatalogoComplicacion,
    CatalogoUbicacion,
    CatalogoVariedad,
    PropagacionLote,
    UserIdentity,
)


class PasswordHasher(Protocol):
    """Puerto para hashing y verificación segura de contraseñas."""

    def hash(self, raw_password: str) -> str: ...
    def verify(self, raw_password: str, password_hash: str) -> bool: ...


class TokenProvider(Protocol):
    """Puerto para emisión y validación de JWT y tokens opacos."""

    def create_access_token(self, identity: UserIdentity) -> str: ...
    def decode_access_token(self, token: str) -> dict[str, Any]: ...
    def generate_opaque_token(self) -> tuple[str, str]: ...
    def hash_token(self, raw_token: str) -> str: ...


class AuditPort(Protocol):
    """Puerto para bitácora inmutable de eventos (BD + JSONL append-only)."""

    async def record(
        self,
        *,
        correlation_id: str,
        usuario_id: UUID | None,
        username: str,
        entidad: str,
        entidad_id: str,
        operacion: str,
        resultado: str,
        fuente: str,
        detalle: dict[str, Any],
        client_mutation_id: str | None = None,
    ) -> None: ...

    async def list_logs(
        self,
        *,
        entidad: str | None = None,
        usuario: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...


class AuthPort(Protocol):
    """Puerto de acceso a usuarios, funcionarios, roles y refresh tokens."""

    async def get_by_username_or_email(self, identifier: str) -> dict[str, Any] | None: ...
    async def get_identity_by_id(self, user_id: UUID) -> UserIdentity | None: ...
    async def list_users(self) -> list[dict[str, Any]]: ...
    async def create_user_with_funcionario(self, data: dict[str, Any]) -> dict[str, Any]: ...
    async def update_user_status_or_roles(
        self, user_id: UUID, activo: bool | None, role_codes: list[str] | None
    ) -> dict[str, Any] | None: ...
    async def store_refresh_token(
        self, usuario_id: UUID, token_hash: str, expires_at: datetime
    ) -> None: ...
    async def get_refresh_token(self, token_hash: str) -> dict[str, Any] | None: ...
    async def revoke_refresh_token(self, token_hash: str) -> None: ...
    async def set_reset_token(
        self, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> None: ...
    async def consume_reset_token(
        self, token_hash: str, new_password_hash: str
    ) -> UUID | None: ...


class ProduccionPort(Protocol):
    """Puerto unificado de persistencia para catálogos y entidades productivas."""

    async def list_variedades(self, since: datetime | None = None) -> list[CatalogoVariedad]: ...
    async def list_ubicaciones(
        self, since: datetime | None = None
    ) -> list[CatalogoUbicacion]: ...
    async def list_complicaciones(
        self, since: datetime | None = None
    ) -> list[CatalogoComplicacion]: ...
    async def save_variedad(self, item: CatalogoVariedad) -> CatalogoVariedad: ...
    async def save_ubicacion(self, item: CatalogoUbicacion) -> CatalogoUbicacion: ...
    async def save_complicacion(self, item: CatalogoComplicacion) -> CatalogoComplicacion: ...

    async def get_entity(self, entity_type: str, entity_id: UUID) -> Any | None: ...
    async def save_entity(self, entity_type: str, entity: Any) -> Any: ...
    async def list_entities(
        self,
        entity_type: str,
        *,
        lote_id: UUID | None = None,
        fecha_inicio: date | None = None,
        fecha_fin: date | None = None,
        since: datetime | None = None,
        include_deleted: bool = False,
    ) -> list[Any]: ...
    async def get_lote_by_codigo(self, codigo_lote: str) -> PropagacionLote | None: ...
    async def sum_bajas_lote(self, lote_id: UUID, exclude_baja_id: UUID | None = None) -> int: ...
    async def list_lote_full_trace(self, lote_id: UUID) -> dict[str, Any]: ...
    async def get_processed_mutation(self, mutation_id: UUID) -> dict[str, Any] | None: ...
    async def save_processed_mutation(
        self,
        *,
        mutation_id: UUID,
        usuario_id: UUID,
        entidad: str,
        entidad_id: UUID,
        operacion: str,
        status: str,
        response_json: dict[str, Any],
    ) -> None: ...
    async def list_roles_summary(self) -> list[dict[str, Any]]: ...
    async def commit(self) -> None: ...


class SyncEntityMap:
    """Tipos de entidad válidos para sincronización offline."""

    CATALOGS = {"variedad", "ubicacion", "tipo_complicacion"}
    PRODUCTION = {
        "propagacion",
        "transplante",
        "planta_madre",
        "extraccion_material",
        "control_fase",
        "cosecha",
        "post_cosecha",
        "baja",
    }
    ALL = CATALOGS | PRODUCTION
    ORDER = [
        "variedad",
        "ubicacion",
        "tipo_complicacion",
        "propagacion",
        "transplante",
        "planta_madre",
        "extraccion_material",
        "control_fase",
        "cosecha",
        "post_cosecha",
        "baja",
    ]
