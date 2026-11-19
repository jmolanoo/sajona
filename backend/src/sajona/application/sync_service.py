"""Motor de sincronización Offline-First (Push idempotente + Pull delta + Conflictos)."""

from datetime import datetime
from typing import Any

from sajona.application.dto import (
    SyncMutationItem,
    SyncMutationOutcome,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
)
from sajona.application.entity_factory import build_and_validate_entity, serialize_entity
from sajona.application.ports import AuditPort, ProduccionPort, SyncEntityMap
from sajona.application.rbac import permission_for_entity_operation, require_permission
from sajona.domain.entities import UserIdentity, utc_now
from sajona.domain.exceptions import DomainError, ValidationError


class SyncService:
    """Orquesta sincronización bidireccional confiable entre IndexedDB y PostgreSQL."""

    def __init__(self, repo: ProduccionPort, audit: AuditPort) -> None:
        self._repo = repo
        self._audit = audit

    async def push(
        self, req: SyncPushRequest, actor: UserIdentity, correlation_id: str
    ) -> SyncPushResponse:
        """Procesa mutaciones pendientes en orden con idempotencia y detección de conflictos."""
        require_permission(actor, "sync:execute")
        outcomes: list[SyncMutationOutcome] = []
        for item in req.mutations:
            outcome = await self._process_single_mutation(item, actor, correlation_id)
            outcomes.append(outcome)
        await self._repo.commit()
        return SyncPushResponse(server_time=utc_now(), results=outcomes)

    async def pull(self, since: datetime | None, actor: UserIdentity) -> SyncPullResponse:
        """Entrega cambios incrementales (incluyendo soft-deletes) desde el cursor `since`."""
        require_permission(actor, "production:read")
        cursor = utc_now()
        changes: dict[str, list[dict[str, Any]]] = {}
        for entity_type in SyncEntityMap.ORDER:
            rows = await self._repo.list_entities(
                entity_type,
                since=since,
                include_deleted=since is not None,
            )
            changes[entity_type] = [serialize_entity(r) for r in rows]
        return SyncPullResponse(server_cursor=cursor, changes=changes)

    async def _process_single_mutation(
        self, item: SyncMutationItem, actor: UserIdentity, correlation_id: str
    ) -> SyncMutationOutcome:
        """Aplica una mutación con verificación de idempotencia, permisos y versión optimista."""
        previous = await self._repo.get_processed_mutation(item.client_mutation_id)
        if previous:
            return SyncMutationOutcome(
                client_mutation_id=item.client_mutation_id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                status="duplicate",
                new_version=previous["response_json"].get("new_version"),
                server_record=previous["response_json"].get("server_record"),
                message="Mutación ya procesada previamente (idempotencia garantizada).",
            )

        try:
            if item.entity_type not in SyncEntityMap.ALL:
                raise ValidationError(f"Tipo de entidad no soportado: '{item.entity_type}'.")
            require_permission(
                actor, permission_for_entity_operation(item.entity_type, item.operation)
            )
            outcome = await self._apply_mutation(item, actor, correlation_id)
        except DomainError as exc:
            outcome = SyncMutationOutcome(
                client_mutation_id=item.client_mutation_id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                status="rejected",
                error_code=exc.code,
                message=exc.message,
            )

        if outcome.status == "applied":
            await self._repo.save_processed_mutation(
                mutation_id=item.client_mutation_id,
                usuario_id=actor.id,
                entidad=item.entity_type,
                entidad_id=item.entity_id,
                operacion=item.operation,
                status=outcome.status,
                response_json=outcome.model_dump(mode="json"),
            )
        return outcome

    async def _apply_mutation(
        self, item: SyncMutationItem, actor: UserIdentity, correlation_id: str
    ) -> SyncMutationOutcome:
        existing = await self._repo.get_entity(item.entity_type, item.entity_id)

        if item.operation == "CREATE":
            if existing:
                return self._conflict_or_existing(item, existing)
            payload = {**item.payload, "id": str(item.entity_id)}
            entity = await build_and_validate_entity(
                item.entity_type, payload, self._repo, actor.id
            )
            saved = await self._repo.save_entity(item.entity_type, entity)
            return await self._record_applied(item, saved, actor, correlation_id)

        if not existing:
            return SyncMutationOutcome(
                client_mutation_id=item.client_mutation_id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                status="rejected",
                error_code="NOT_FOUND",
                message="El registro objetivo ya no existe en el servidor.",
            )

        if item.base_version != existing.version:
            return SyncMutationOutcome(
                client_mutation_id=item.client_mutation_id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                status="conflict",
                new_version=existing.version,
                server_record=serialize_entity(existing),
                error_code="VERSION_CONFLICT",
                message=(
                    f"Conflicto detectado: base local v{item.base_version} vs "
                    f"servidor v{existing.version}."
                ),
            )

        if item.operation == "DELETE":
            now = utc_now()
            existing.deleted_at = now
            existing.updated_at = now
            existing.version += 1
            saved = await self._repo.save_entity(item.entity_type, existing)
            return await self._record_applied(item, saved, actor, correlation_id)

        payload = {**item.payload, "id": str(item.entity_id)}
        updated = await build_and_validate_entity(
            item.entity_type, payload, self._repo, actor.id, existing=existing
        )
        saved = await self._repo.save_entity(item.entity_type, updated)
        return await self._record_applied(item, saved, actor, correlation_id)

    def _conflict_or_existing(
        self, item: SyncMutationItem, existing: Any
    ) -> SyncMutationOutcome:
        return SyncMutationOutcome(
            client_mutation_id=item.client_mutation_id,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            status="conflict",
            new_version=existing.version,
            server_record=serialize_entity(existing),
            error_code="ALREADY_EXISTS",
            message="El identificador ya fue creado previamente en el servidor.",
        )

    async def _record_applied(
        self,
        item: SyncMutationItem,
        saved: Any,
        actor: UserIdentity,
        correlation_id: str,
    ) -> SyncMutationOutcome:
        serialized = serialize_entity(saved)
        await self._audit.record(
            correlation_id=correlation_id,
            usuario_id=actor.id,
            username=actor.username,
            entidad=item.entity_type,
            entidad_id=str(item.entity_id),
            operacion=item.operation,
            resultado="OK",
            fuente="offline_sync",
            client_mutation_id=str(item.client_mutation_id),
            detalle={"version": saved.version},
        )
        return SyncMutationOutcome(
            client_mutation_id=item.client_mutation_id,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            status="applied",
            new_version=saved.version,
            server_record=serialized,
        )
