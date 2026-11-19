"""Inyección de dependencias FastAPI y resolución de identidad JWT."""

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from sajona.application.auth_service import AuthService
from sajona.application.produccion_service import ProduccionService
from sajona.application.sync_service import SyncService
from sajona.config import Settings, get_settings
from sajona.domain.entities import UserIdentity
from sajona.domain.exceptions import UnauthorizedError
from sajona.infrastructure.audit_logger import DualAuditLogger
from sajona.infrastructure.repositories import (
    SqlAlchemyAuthRepository,
    SqlAlchemyProduccionRepository,
)
from sajona.infrastructure.security import Argon2PasswordHasher, JwtTokenProvider

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Obtiene una sesión SQLAlchemy desde el estado de la aplicación."""
    factory = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def get_correlation_id(request: Request) -> str:
    """Extrae el ID de correlación inyectado por el middleware."""
    cid: str = getattr(request.state, "correlation_id", "unknown")
    return cid


def get_token_provider(settings: Annotated[Settings, Depends(get_settings)]) -> JwtTokenProvider:
    return JwtTokenProvider(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        ttl_minutes=settings.access_token_minutes,
    )


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    tokens: Annotated[JwtTokenProvider, Depends(get_token_provider)],
) -> AuthService:
    return AuthService(
        auth_port=SqlAlchemyAuthRepository(session),
        audit_port=DualAuditLogger(session, settings.audit_log_dir),
        hasher=Argon2PasswordHasher(),
        tokens=tokens,
        access_ttl_minutes=settings.access_token_minutes,
        refresh_ttl_days=settings.refresh_token_days,
    )


def get_produccion_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProduccionService:
    return ProduccionService(
        repo=SqlAlchemyProduccionRepository(session),
        audit=DualAuditLogger(session, settings.audit_log_dir),
    )


def get_sync_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SyncService:
    return SyncService(
        repo=SqlAlchemyProduccionRepository(session),
        audit=DualAuditLogger(session, settings.audit_log_dir),
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    tokens: Annotated[JwtTokenProvider, Depends(get_token_provider)],
) -> UserIdentity:
    """Valida el JWT Bearer y carga la identidad RBAC vigente en BD."""
    if not credentials:
        raise UnauthorizedError("Se requiere cabecera Authorization Bearer.")
    payload = tokens.decode_access_token(credentials.credentials)
    user_id = UUID(str(payload["sub"]))
    identity = await SqlAlchemyAuthRepository(session).get_identity_by_id(user_id)
    if not identity or not identity.activo:
        raise UnauthorizedError("Usuario inactivo o no encontrado.")
    return identity
