"""Adaptador de bitácora inmutable en PostgreSQL y archivo JSONL append-only."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from sajona.infrastructure.models import AuditLogModel


class DualAuditLogger:
    """Registra eventos de auditoría en BD relacional y archivo JSONL append-only."""

    def __init__(self, session: AsyncSession, log_dir: str) -> None:
        self._session = session
        self._log_dir = Path(log_dir)

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
    ) -> None:
        now = datetime.now(UTC)
        entry_id = uuid4()
        row = AuditLogModel(
            id=entry_id,
            correlation_id=correlation_id,
            usuario_id=usuario_id,
            username=username,
            entidad=entidad,
            entidad_id=entidad_id,
            operacion=operacion,
            resultado=resultado,
            fuente=fuente,
            client_mutation_id=client_mutation_id,
            detalle_json=detalle,
            created_at=now,
        )
        self._session.add(row)
        self._append_jsonl(
            {
                "id": str(entry_id),
                "correlation_id": correlation_id,
                "usuario_id": str(usuario_id) if usuario_id else None,
                "username": username,
                "entidad": entidad,
                "entidad_id": entidad_id,
                "operacion": operacion,
                "resultado": resultado,
                "fuente": fuente,
                "client_mutation_id": client_mutation_id,
                "detalle": detalle,
                "created_at": now.isoformat(),
            }
        )

    async def list_logs(
        self,
        *,
        entidad: str | None = None,
        usuario: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        stmt = select(AuditLogModel).order_by(desc(AuditLogModel.created_at)).limit(limit)
        if entidad:
            stmt = stmt.where(AuditLogModel.entidad == entidad)
        if usuario:
            stmt = stmt.where(AuditLogModel.username.ilike(f"%{usuario}%"))
        rows = (await self._session.scalars(stmt)).all()
        return [
            {
                "id": str(r.id),
                "correlation_id": r.correlation_id,
                "usuario_id": str(r.usuario_id) if r.usuario_id else None,
                "username": r.username,
                "entidad": r.entidad,
                "entidad_id": r.entidad_id,
                "operacion": r.operacion,
                "resultado": r.resultado,
                "fuente": r.fuente,
                "client_mutation_id": r.client_mutation_id,
                "detalle": r.detalle_json,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]

    def _append_jsonl(self, payload: dict[str, Any]) -> None:
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            log_file = self._log_dir / "audit.jsonl"
            with log_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except OSError:
            pass
