"""Casos de uso operativos online, trazabilidad por lote y reportes."""

from datetime import date
from typing import Any
from uuid import UUID

from sajona.application.entity_factory import build_and_validate_entity, serialize_entity
from sajona.application.ports import AuditPort, ProduccionPort, SyncEntityMap
from sajona.application.rbac import permission_for_entity_operation, require_permission
from sajona.domain.entities import UserIdentity, utc_now
from sajona.domain.exceptions import ConflictError, NotFoundError, ValidationError


class ProduccionService:
    """Operaciones CRUD auditadas, consultas de trazabilidad y reportes."""

    def __init__(self, repo: ProduccionPort, audit: AuditPort) -> None:
        self._repo = repo
        self._audit = audit

    async def list_items(
        self,
        entity_type: str,
        actor: UserIdentity,
        *,
        lote_id: UUID | None = None,
        fecha_inicio: date | None = None,
        fecha_fin: date | None = None,
    ) -> list[dict[str, Any]]:
        """Lista entidades activas filtradas con verificación RBAC."""
        perm = "catalogs:read" if entity_type in SyncEntityMap.CATALOGS else "production:read"
        require_permission(actor, perm)
        if entity_type not in SyncEntityMap.ALL:
            raise ValidationError(f"Tipo de entidad desconocido: '{entity_type}'.")
        rows = await self._repo.list_entities(
            entity_type,
            lote_id=lote_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        return [serialize_entity(r) for r in rows]

    async def create_item(
        self,
        entity_type: str,
        payload: dict[str, Any],
        actor: UserIdentity,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Crea un nuevo registro aplicando reglas de dominio y auditoría."""
        require_permission(actor, permission_for_entity_operation(entity_type, "CREATE"))
        entity = await build_and_validate_entity(entity_type, payload, self._repo, actor.id)
        saved = await self._repo.save_entity(entity_type, entity)
        result = serialize_entity(saved)
        await self._audit.record(
            correlation_id=correlation_id,
            usuario_id=actor.id,
            username=actor.username,
            entidad=entity_type,
            entidad_id=str(saved.id),
            operacion="CREATE",
            resultado="OK",
            fuente="online",
            detalle=result,
        )
        await self._repo.commit()
        return result

    async def update_item(
        self,
        entity_type: str,
        entity_id: UUID,
        payload: dict[str, Any],
        actor: UserIdentity,
        correlation_id: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        """Actualiza un registro verificando concurrencia optimista."""
        require_permission(actor, permission_for_entity_operation(entity_type, "UPDATE"))
        existing = await self._repo.get_entity(entity_type, entity_id)
        if not existing or existing.deleted_at is not None:
            raise NotFoundError(entity_type, str(entity_id))
        if expected_version is not None and existing.version != expected_version:
            raise ConflictError(
                f"Conflicto de versión en {entity_type}: esperada {expected_version}, "
                f"vigente {existing.version}."
            )
        payload["id"] = str(entity_id)
        updated_entity = await build_and_validate_entity(
            entity_type, payload, self._repo, actor.id, existing=existing
        )
        saved = await self._repo.save_entity(entity_type, updated_entity)
        result = serialize_entity(saved)
        await self._audit.record(
            correlation_id=correlation_id,
            usuario_id=actor.id,
            username=actor.username,
            entidad=entity_type,
            entidad_id=str(entity_id),
            operacion="UPDATE",
            resultado="OK",
            fuente="online",
            detalle={"version": saved.version},
        )
        await self._repo.commit()
        return result

    async def delete_item(
        self,
        entity_type: str,
        entity_id: UUID,
        actor: UserIdentity,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Ejecuta borrado lógico (soft-delete) para mantener trazabilidad y sync delta."""
        require_permission(actor, permission_for_entity_operation(entity_type, "DELETE"))
        existing = await self._repo.get_entity(entity_type, entity_id)
        if not existing or existing.deleted_at is not None:
            raise NotFoundError(entity_type, str(entity_id))
        now = utc_now()
        existing.deleted_at = now
        existing.updated_at = now
        existing.version += 1
        saved = await self._repo.save_entity(entity_type, existing)
        await self._audit.record(
            correlation_id=correlation_id,
            usuario_id=actor.id,
            username=actor.username,
            entidad=entity_type,
            entidad_id=str(entity_id),
            operacion="DELETE",
            resultado="OK",
            fuente="online",
            detalle={"version": saved.version},
        )
        await self._repo.commit()
        return serialize_entity(saved)

    async def get_lote_traceability(
        self, lote_id: UUID, actor: UserIdentity
    ) -> dict[str, Any]:
        """Retorna la traza completa 360° de un lote desde propagación hasta postcosecha."""
        require_permission(actor, "reports:read")
        trace = await self._repo.list_lote_full_trace(lote_id)
        if not trace:
            raise NotFoundError("Lote", str(lote_id))
        return trace

    async def get_audit_logs(
        self,
        actor: UserIdentity,
        *,
        entidad: str | None = None,
        usuario: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Consulta registros de bitácora inmutable."""
        require_permission(actor, "audit:read")
        return await self._audit.list_logs(entidad=entidad, usuario=usuario, limit=limit)

    async def list_roles(self, actor: UserIdentity) -> list[dict[str, Any]]:
        """Lista roles y permisos RBAC configurados."""
        require_permission(actor, "users:read")
        return await self._repo.list_roles_summary()
