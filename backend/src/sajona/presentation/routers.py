"""Definición de rutas REST v1 de SAJONA."""

from datetime import date, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, Query, Request, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sajona.application.auth_service import AuthService
from sajona.application.dto import (
    AuthTokenResponse,
    CreateUserRequest,
    LoginRequest,
    PasswordResetConfirmDTO,
    PasswordResetRequestDTO,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
    UpdateUserRequest,
)
from sajona.application.produccion_service import ProduccionService
from sajona.application.sync_service import SyncService
from sajona.config import Settings, get_settings
from sajona.domain.entities import UserIdentity
from sajona.domain.exceptions import UnauthorizedError
from sajona.presentation.dependencies import (
    get_auth_service,
    get_correlation_id,
    get_current_user,
    get_db_session,
    get_produccion_service,
    get_sync_service,
)

REFRESH_COOKIE_NAME = "sajona_refresh"

health_router = APIRouter(tags=["Salud"])
auth_router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["Administración y Auditoría"])
entities_router = APIRouter(prefix="/api/v1/entities", tags=["Operación Productiva"])
sync_router = APIRouter(prefix="/api/v1/sync", tags=["Sincronización Offline-First"])


def _set_refresh_cookie(
    response: Response, raw_token: str, settings: Settings, request: Request
) -> None:
    is_https = (
        settings.cookie_secure
        or request.headers.get("x-forwarded-proto", "").lower() == "https"
        or request.url.scheme == "https"
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=is_https,
        max_age=settings.refresh_token_days * 86400,
        path="/api/v1/auth",
    )


@health_router.get("/health")
@health_router.get("/api/v1/health")
async def healthcheck(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    """Verifica disponibilidad del servicio y conexión a PostgreSQL."""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "version": settings.app_version}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "database": "disconnected", "version": settings.app_version}


@auth_router.post("/login", response_model=AuthTokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> AuthTokenResponse:
    token_resp, raw_refresh = await service.login(req, correlation_id)
    _set_refresh_cookie(response, raw_refresh, settings, request)
    return token_resp


@auth_router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_session(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    sajona_refresh: Annotated[str | None, Cookie()] = None,
) -> AuthTokenResponse:
    if not sajona_refresh:
        raise UnauthorizedError("No se encontró cookie de actualización de sesión.")
    token_resp, new_refresh = await service.refresh(sajona_refresh, correlation_id)
    _set_refresh_cookie(response, new_refresh, settings, request)
    return token_resp


@auth_router.post("/logout")
async def logout(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    sajona_refresh: Annotated[str | None, Cookie()] = None,
) -> dict[str, str]:
    await service.logout(sajona_refresh, actor, correlation_id)
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/v1/auth")
    return {"status": "logged_out"}


@auth_router.get("/me")
async def me(actor: Annotated[UserIdentity, Depends(get_current_user)]) -> dict[str, Any]:
    return {
        "id": str(actor.id),
        "username": actor.username,
        "email": actor.email,
        "full_name": actor.full_name,
        "roles": [r.value for r in actor.roles],
        "permissions": actor.permissions,
        "activo": actor.activo,
    }


@auth_router.post("/password-reset/request")
async def request_reset(
    req: PasswordResetRequestDTO,
    service: Annotated[AuthService, Depends(get_auth_service)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> dict[str, str]:
    return await service.request_password_reset(req, correlation_id)


@auth_router.post("/password-reset/confirm")
async def confirm_reset(
    req: PasswordResetConfirmDTO,
    service: Annotated[AuthService, Depends(get_auth_service)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> dict[str, str]:
    await service.confirm_password_reset(req, correlation_id)
    return {"status": "password_updated"}


@admin_router.get("/users")
async def list_users(
    service: Annotated[AuthService, Depends(get_auth_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
) -> list[dict[str, object]]:
    return await service.list_users(actor)


@admin_router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    req: CreateUserRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> dict[str, object]:
    return await service.create_user(req, actor, correlation_id)


@admin_router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    req: UpdateUserRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> dict[str, object]:
    return await service.update_user(user_id, req, actor, correlation_id)


@admin_router.get("/roles")
async def list_roles(
    service: Annotated[ProduccionService, Depends(get_produccion_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    return await service.list_roles(actor)


@admin_router.get("/audit-logs")
async def list_audit_logs(
    service: Annotated[ProduccionService, Depends(get_produccion_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    entidad: str | None = None,
    usuario: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    return await service.get_audit_logs(actor, entidad=entidad, usuario=usuario, limit=limit)


@entities_router.get("/lotes/{lote_id}/trazabilidad")
async def get_lote_trazabilidad(
    lote_id: UUID,
    service: Annotated[ProduccionService, Depends(get_produccion_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
) -> dict[str, Any]:
    return await service.get_lote_traceability(lote_id, actor)


@entities_router.get("/{entity_type}")
async def list_entities(
    entity_type: str,
    service: Annotated[ProduccionService, Depends(get_produccion_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    lote_id: UUID | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
) -> list[dict[str, Any]]:
    return await service.list_items(
        entity_type,
        actor,
        lote_id=lote_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


@entities_router.post("/{entity_type}", status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_type: str,
    payload: dict[str, Any],
    service: Annotated[ProduccionService, Depends(get_produccion_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> dict[str, Any]:
    return await service.create_item(entity_type, payload, actor, correlation_id)


@entities_router.put("/{entity_type}/{entity_id}")
async def update_entity(
    entity_type: str,
    entity_id: UUID,
    payload: dict[str, Any],
    service: Annotated[ProduccionService, Depends(get_produccion_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    if_match_version: Annotated[int | None, Header(alias="X-Expected-Version")] = None,
) -> dict[str, Any]:
    return await service.update_item(
        entity_type,
        entity_id,
        payload,
        actor,
        correlation_id,
        expected_version=if_match_version,
    )


@entities_router.delete("/{entity_type}/{entity_id}")
async def delete_entity(
    entity_type: str,
    entity_id: UUID,
    service: Annotated[ProduccionService, Depends(get_produccion_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> dict[str, Any]:
    return await service.delete_item(entity_type, entity_id, actor, correlation_id)


@sync_router.post("/push", response_model=SyncPushResponse)
async def sync_push(
    req: SyncPushRequest,
    service: Annotated[SyncService, Depends(get_sync_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> SyncPushResponse:
    return await service.push(req, actor, correlation_id)


@sync_router.get("/pull", response_model=SyncPullResponse)
async def sync_pull(
    service: Annotated[SyncService, Depends(get_sync_service)],
    actor: Annotated[UserIdentity, Depends(get_current_user)],
    since: datetime | None = None,
) -> SyncPullResponse:
    return await service.pull(since, actor)
