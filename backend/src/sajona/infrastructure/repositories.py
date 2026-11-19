"""Implementaciones SQLAlchemy de los puertos AuthPort y ProduccionPort."""

from datetime import UTC, date, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from sajona.application.entity_factory import serialize_entity
from sajona.application.rbac import resolve_permissions
from sajona.domain.entities import (
    CatalogoComplicacion,
    CatalogoUbicacion,
    CatalogoVariedad,
    PropagacionLote,
    UserIdentity,
)
from sajona.domain.enums import RoleCode
from sajona.infrastructure.mappers import ENTITY_SPECS, apply_entity_to_orm, orm_to_entity
from sajona.infrastructure.models import (
    BajaModel,
    FuncionarioModel,
    ProcessedMutationModel,
    PropagacionModel,
    RefreshTokenModel,
    RolModel,
    UsuarioModel,
    UsuarioRolModel,
)


class SqlAlchemyAuthRepository:
    """Repositorio de usuarios, funcionarios, roles y tokens."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_username_or_email(self, identifier: str) -> dict[str, Any] | None:
        stmt = select(UsuarioModel).where(
            UsuarioModel.deleted_at.is_(None),
            or_(UsuarioModel.username == identifier, UsuarioModel.email == identifier),
        )
        user = await self._session.scalar(stmt)
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "password_hash": user.password_hash,
            "activo": user.activo,
        }

    async def get_identity_by_id(self, user_id: UUID) -> UserIdentity | None:
        user = await self._session.get(UsuarioModel, user_id)
        if not user or user.deleted_at is not None:
            return None
        full_name = user.username
        if user.funcionario_id:
            func_obj = await self._session.get(FuncionarioModel, user.funcionario_id)
            if func_obj:
                full_name = f"{func_obj.nombres} {func_obj.apellidos}".strip()
        role_stmt = (
            select(RolModel.codigo)
            .join(UsuarioRolModel, UsuarioRolModel.rol_id == RolModel.id)
            .where(UsuarioRolModel.usuario_id == user.id, RolModel.activo.is_(True))
        )
        codes = [RoleCode(code) for code in (await self._session.scalars(role_stmt)).all()]
        return UserIdentity(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=full_name,
            roles=codes,
            permissions=resolve_permissions(codes),
            activo=user.activo,
        )

    async def list_users(self) -> list[dict[str, Any]]:
        users = (
            await self._session.scalars(
                select(UsuarioModel).where(UsuarioModel.deleted_at.is_(None))
            )
        ).all()
        result: list[dict[str, Any]] = []
        for u in users:
            identity = await self.get_identity_by_id(u.id)
            if identity:
                result.append(
                    {
                        "id": str(identity.id),
                        "username": identity.username,
                        "email": identity.email,
                        "full_name": identity.full_name,
                        "roles": [r.value for r in identity.roles],
                        "activo": identity.activo,
                        "created_at": u.created_at.isoformat(),
                    }
                )
        return result

    async def create_user_with_funcionario(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC)
        func_id = uuid4()
        user_id = uuid4()
        self._session.add(
            FuncionarioModel(
                id=func_id,
                nombres=data["nombres"],
                apellidos=data["apellidos"],
                numero_identificacion=data["numero_identificacion"],
                correo=data["email"],
                telefono=data["telefono"],
                activo=True,
                version=1,
                created_at=now,
                updated_at=now,
            )
        )
        self._session.add(
            UsuarioModel(
                id=user_id,
                funcionario_id=func_id,
                username=data["username"],
                email=data["email"],
                password_hash=data["password_hash"],
                activo=True,
                version=1,
                created_at=now,
                updated_at=now,
            )
        )
        await self._assign_roles(user_id, data["roles"])
        await self._session.commit()
        identity = await self.get_identity_by_id(user_id)
        assert identity is not None
        return {
            "id": str(identity.id),
            "username": identity.username,
            "email": identity.email,
            "full_name": identity.full_name,
            "roles": [r.value for r in identity.roles],
            "activo": identity.activo,
        }

    async def update_user_status_or_roles(
        self, user_id: UUID, activo: bool | None, role_codes: list[str] | None
    ) -> dict[str, Any] | None:
        user = await self._session.get(UsuarioModel, user_id)
        if not user or user.deleted_at is not None:
            return None
        if activo is not None:
            user.activo = activo
        if role_codes is not None:
            existing_links = (
                await self._session.scalars(
                    select(UsuarioRolModel).where(UsuarioRolModel.usuario_id == user_id)
                )
            ).all()
            for link in existing_links:
                await self._session.delete(link)
            await self._session.flush()
            await self._assign_roles(user_id, role_codes)
        user.updated_at = datetime.now(UTC)
        user.version += 1
        await self._session.commit()
        identity = await self.get_identity_by_id(user_id)
        assert identity is not None
        return {
            "id": str(identity.id),
            "username": identity.username,
            "email": identity.email,
            "full_name": identity.full_name,
            "roles": [r.value for r in identity.roles],
            "activo": identity.activo,
        }

    async def store_refresh_token(
        self, usuario_id: UUID, token_hash: str, expires_at: datetime
    ) -> None:
        self._session.add(
            RefreshTokenModel(
                id=uuid4(),
                usuario_id=usuario_id,
                token_hash=token_hash,
                expires_at=expires_at,
                created_at=datetime.now(UTC),
            )
        )
        await self._session.commit()

    async def get_refresh_token(self, token_hash: str) -> dict[str, Any] | None:
        row = await self._session.scalar(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        if not row:
            return None
        exp = row.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        return {
            "usuario_id": row.usuario_id,
            "expires_at": exp,
            "revoked_at": row.revoked_at,
        }

    async def revoke_refresh_token(self, token_hash: str) -> None:
        row = await self._session.scalar(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        if row and row.revoked_at is None:
            row.revoked_at = datetime.now(UTC)
            await self._session.commit()

    async def set_reset_token(
        self, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> None:
        user = await self._session.get(UsuarioModel, user_id)
        if user:
            user.reset_token_hash = token_hash
            user.reset_token_expires = expires_at
            await self._session.commit()

    async def consume_reset_token(
        self, token_hash: str, new_password_hash: str
    ) -> UUID | None:
        now = datetime.now(UTC)
        user = await self._session.scalar(
            select(UsuarioModel).where(UsuarioModel.reset_token_hash == token_hash)
        )
        if not user or not user.reset_token_expires:
            return None
        exp = user.reset_token_expires
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp <= now:
            return None
        user.password_hash = new_password_hash
        user.fecha_cambio_password = now
        user.reset_token_hash = None
        user.reset_token_expires = None
        user.version += 1
        user.updated_at = now
        await self._session.commit()
        return user.id

    async def _assign_roles(self, user_id: UUID, role_codes: list[str]) -> None:
        roles = (
            await self._session.scalars(
                select(RolModel).where(RolModel.codigo.in_(role_codes))
            )
        ).all()
        for rol in roles:
            self._session.add(UsuarioRolModel(usuario_id=user_id, rol_id=rol.id))


class SqlAlchemyProduccionRepository:
    """Repositorio unificado para catálogos, producción, trazabilidad y sync."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_variedades(self, since: datetime | None = None) -> list[CatalogoVariedad]:
        return await self.list_entities("variedad", since=since, include_deleted=since is not None)

    async def list_ubicaciones(self, since: datetime | None = None) -> list[CatalogoUbicacion]:
        return await self.list_entities("ubicacion", since=since, include_deleted=since is not None)

    async def list_complicaciones(
        self, since: datetime | None = None
    ) -> list[CatalogoComplicacion]:
        return await self.list_entities(
            "tipo_complicacion", since=since, include_deleted=since is not None
        )

    async def save_variedad(self, item: CatalogoVariedad) -> CatalogoVariedad:
        return cast(CatalogoVariedad, await self.save_entity("variedad", item))

    async def save_ubicacion(self, item: CatalogoUbicacion) -> CatalogoUbicacion:
        return cast(CatalogoUbicacion, await self.save_entity("ubicacion", item))

    async def save_complicacion(self, item: CatalogoComplicacion) -> CatalogoComplicacion:
        return cast(CatalogoComplicacion, await self.save_entity("tipo_complicacion", item))

    async def get_entity(self, entity_type: str, entity_id: UUID) -> Any | None:
        model_cls, _, _ = ENTITY_SPECS[entity_type]
        row = await self._session.get(model_cls, entity_id)
        return orm_to_entity(entity_type, row) if row else None

    async def save_entity(self, entity_type: str, entity: Any) -> Any:
        model_cls, _, _ = ENTITY_SPECS[entity_type]
        existing = await self._session.get(model_cls, entity.id)
        orm_obj = apply_entity_to_orm(entity_type, entity, existing)
        if not existing:
            self._session.add(orm_obj)
        await self._session.flush()
        return orm_to_entity(entity_type, orm_obj)

    async def list_entities(
        self,
        entity_type: str,
        *,
        lote_id: UUID | None = None,
        fecha_inicio: date | None = None,
        fecha_fin: date | None = None,
        since: datetime | None = None,
        include_deleted: bool = False,
    ) -> list[Any]:
        model_cls, _, date_col_name = ENTITY_SPECS[entity_type]
        stmt = select(model_cls)
        if not include_deleted:
            stmt = stmt.where(model_cls.deleted_at.is_(None))
        if lote_id is not None and hasattr(model_cls, "lote_id"):
            stmt = stmt.where(model_cls.lote_id == lote_id)
        if since is not None:
            stmt = stmt.where(model_cls.updated_at >= since)
        if date_col_name and (fecha_inicio or fecha_fin):
            date_col = getattr(model_cls, date_col_name)
            if fecha_inicio:
                stmt = stmt.where(date_col >= fecha_inicio)
            if fecha_fin:
                stmt = stmt.where(date_col <= fecha_fin)
        stmt = stmt.order_by(model_cls.created_at.desc())
        rows = (await self._session.scalars(stmt)).all()
        return [orm_to_entity(entity_type, r) for r in rows]

    async def get_lote_by_codigo(self, codigo_lote: str) -> PropagacionLote | None:
        row = await self._session.scalar(
            select(PropagacionModel).where(
                PropagacionModel.codigo_lote == codigo_lote,
                PropagacionModel.deleted_at.is_(None),
            )
        )
        return orm_to_entity("propagacion", row) if row else None

    async def sum_bajas_lote(
        self, lote_id: UUID, exclude_baja_id: UUID | None = None
    ) -> int:
        stmt = select(func.coalesce(func.sum(BajaModel.cantidad), 0)).where(
            BajaModel.lote_id == lote_id, BajaModel.deleted_at.is_(None)
        )
        if exclude_baja_id:
            stmt = stmt.where(BajaModel.id != exclude_baja_id)
        total = await self._session.scalar(stmt)
        return int(total or 0)

    async def list_lote_full_trace(self, lote_id: UUID) -> dict[str, Any]:
        lote = await self.get_entity("propagacion", lote_id)
        if not lote or lote.deleted_at is not None:
            return {}
        bajas_total = await self.sum_bajas_lote(lote_id)
        trace: dict[str, Any] = {
            "lote": serialize_entity(lote),
            "resumen": {
                "cantidad_inicial": lote.cantidad_material,
                "bajas_totales": bajas_total,
                "saldo_vivo": max(lote.cantidad_material - bajas_total, 0),
            },
        }
        related = [
            "transplante",
            "planta_madre",
            "extraccion_material",
            "control_fase",
            "cosecha",
            "post_cosecha",
            "baja",
        ]
        for key in related:
            items = await self.list_entities(key, lote_id=lote_id)
            trace[key] = [serialize_entity(i) for i in items]
        return trace

    async def get_processed_mutation(self, mutation_id: UUID) -> dict[str, Any] | None:
        row = await self._session.get(ProcessedMutationModel, mutation_id)
        if not row:
            return None
        return {"status": row.status, "response_json": row.response_json}

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
    ) -> None:
        self._session.add(
            ProcessedMutationModel(
                client_mutation_id=mutation_id,
                usuario_id=usuario_id,
                entidad=entidad,
                entidad_id=entidad_id,
                operacion=operacion,
                status=status,
                response_json=response_json,
                processed_at=datetime.now(UTC),
            )
        )
        await self._session.flush()

    async def list_roles_summary(self) -> list[dict[str, Any]]:
        roles = (await self._session.scalars(select(RolModel))).all()
        return [
            {
                "id": str(r.id),
                "codigo": r.codigo,
                "descripcion": r.descripcion,
                "activo": r.activo,
            }
            for r in roles
        ]

    async def commit(self) -> None:
        await self._session.commit()
