"""Casos de uso de autenticación, sesiones, recuperación y administración de usuarios."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sajona.application.dto import (
    AuthTokenResponse,
    CreateUserRequest,
    LoginRequest,
    PasswordResetConfirmDTO,
    PasswordResetRequestDTO,
    UpdateUserRequest,
    UserProfileDTO,
)
from sajona.application.ports import AuditPort, AuthPort, PasswordHasher, TokenProvider
from sajona.application.rbac import require_permission
from sajona.domain.entities import UserIdentity
from sajona.domain.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


def _to_profile(identity: UserIdentity) -> UserProfileDTO:
    return UserProfileDTO(
        id=identity.id,
        username=identity.username,
        email=identity.email,
        full_name=identity.full_name,
        roles=identity.roles,
        permissions=identity.permissions,
        activo=identity.activo,
    )


class AuthService:
    """Gestión de acceso, rotación de refresh tokens, recuperación y usuarios."""

    def __init__(
        self,
        auth_port: AuthPort,
        audit_port: AuditPort,
        hasher: PasswordHasher,
        tokens: TokenProvider,
        access_ttl_minutes: int = 15,
        refresh_ttl_days: int = 7,
    ) -> None:
        self._auth = auth_port
        self._audit = audit_port
        self._hasher = hasher
        self._tokens = tokens
        self._access_ttl_minutes = access_ttl_minutes
        self._refresh_ttl_days = refresh_ttl_days

    async def login(
        self, req: LoginRequest, correlation_id: str
    ) -> tuple[AuthTokenResponse, str]:
        """Autentica credenciales y emite access + refresh token."""
        user_row = await self._auth.get_by_username_or_email(req.identifier.strip())
        if not user_row or not self._hasher.verify(req.password, user_row["password_hash"]):
            await self._audit.record(
                correlation_id=correlation_id,
                usuario_id=None,
                username=req.identifier,
                entidad="usuario",
                entidad_id="login",
                operacion="LOGIN",
                resultado="DENIED",
                fuente="online",
                detalle={"reason": "invalid_credentials"},
            )
            raise UnauthorizedError("Usuario o contraseña incorrectos.")

        identity = await self._auth.get_identity_by_id(user_row["id"])
        if not identity or not identity.activo:
            raise UnauthorizedError("Cuenta deshabilitada o inexistente.")

        return await self._issue_session(identity, correlation_id, "LOGIN")

    async def refresh(
        self, raw_refresh_token: str, correlation_id: str
    ) -> tuple[AuthTokenResponse, str]:
        """Rota el refresh token opaco manteniendo trazabilidad de sesión."""
        token_hash = self._tokens.hash_token(raw_refresh_token)
        stored = await self._auth.get_refresh_token(token_hash)
        now = datetime.now(UTC)
        if not stored or stored["revoked_at"] is not None or stored["expires_at"] <= now:
            raise UnauthorizedError("Sesión expirada o revocada; inicie sesión nuevamente.")

        await self._auth.revoke_refresh_token(token_hash)
        identity = await self._auth.get_identity_by_id(stored["usuario_id"])
        if not identity or not identity.activo:
            raise UnauthorizedError("Cuenta inactiva.")

        return await self._issue_session(identity, correlation_id, "REFRESH_TOKEN")

    async def logout(
        self, raw_refresh_token: str | None, identity: UserIdentity, correlation_id: str
    ) -> None:
        """Revoca el token de refresco vigente y audita el cierre de sesión."""
        if raw_refresh_token:
            await self._auth.revoke_refresh_token(self._tokens.hash_token(raw_refresh_token))
        await self._audit.record(
            correlation_id=correlation_id,
            usuario_id=identity.id,
            username=identity.username,
            entidad="usuario",
            entidad_id=str(identity.id),
            operacion="LOGOUT",
            resultado="OK",
            fuente="online",
            detalle={},
        )

    async def request_password_reset(
        self, req: PasswordResetRequestDTO, correlation_id: str
    ) -> dict[str, str]:
        """Genera un token de recuperación de un solo uso sin filtrar existencia de cuenta."""
        user_row = await self._auth.get_by_username_or_email(req.identifier.strip())
        if user_row:
            raw_token, token_hash = self._tokens.generate_opaque_token()
            expires_at = datetime.now(UTC) + timedelta(minutes=30)
            await self._auth.set_reset_token(user_row["id"], token_hash, expires_at)
            await self._audit.record(
                correlation_id=correlation_id,
                usuario_id=user_row["id"],
                username=user_row["username"],
                entidad="usuario",
                entidad_id=str(user_row["id"]),
                operacion="PASSWORD_RESET_REQUEST",
                resultado="OK",
                fuente="online",
                detalle={"expires_at": expires_at.isoformat()},
            )
            return {
                "message": (
                    "Si la cuenta existe, se generó una solicitud de restablecimiento."
                ),
                "reset_token_preview": raw_token,
            }
        return {"message": "Si la cuenta existe, se generó una solicitud de restablecimiento."}

    async def confirm_password_reset(
        self, req: PasswordResetConfirmDTO, correlation_id: str
    ) -> None:
        """Valida el token temporal y actualiza el hash Argon2id de contraseña."""
        token_hash = self._tokens.hash_token(req.token)
        new_hash = self._hasher.hash(req.new_password)
        user_id = await self._auth.consume_reset_token(token_hash, new_hash)
        if not user_id:
            raise ValidationError("Token de recuperación inválido o expirado.")
        await self._audit.record(
            correlation_id=correlation_id,
            usuario_id=user_id,
            username=str(user_id),
            entidad="usuario",
            entidad_id=str(user_id),
            operacion="PASSWORD_RESET_CONFIRM",
            resultado="OK",
            fuente="online",
            detalle={},
        )

    async def list_users(self, actor: UserIdentity) -> list[dict[str, object]]:
        """Lista usuarios y funcionarios registrados (solo ADMIN)."""
        require_permission(actor, "users:read")
        return await self._auth.list_users()

    async def create_user(
        self, req: CreateUserRequest, actor: UserIdentity, correlation_id: str
    ) -> dict[str, object]:
        """Crea funcionario y usuario asociado con roles RBAC."""
        require_permission(actor, "users:write")
        existing = await self._auth.get_by_username_or_email(req.username.strip())
        if existing or await self._auth.get_by_username_or_email(str(req.email)):
            raise ConflictError("Ya existe un usuario con ese nombre o correo.", "USER_EXISTS")
        data = req.model_dump()
        data["password_hash"] = self._hasher.hash(req.password)
        data["roles"] = [r.value for r in req.roles]
        created = await self._auth.create_user_with_funcionario(data)
        await self._audit.record(
            correlation_id=correlation_id,
            usuario_id=actor.id,
            username=actor.username,
            entidad="usuario",
            entidad_id=str(created["id"]),
            operacion="CREATE",
            resultado="OK",
            fuente="online",
            detalle={"username": req.username, "roles": data["roles"]},
        )
        return created

    async def update_user(
        self, user_id: UUID, req: UpdateUserRequest, actor: UserIdentity, correlation_id: str
    ) -> dict[str, object]:
        """Actualiza estado activo o roles asignados de un usuario."""
        require_permission(actor, "users:write")
        roles_str = [r.value for r in req.roles] if req.roles is not None else None
        updated = await self._auth.update_user_status_or_roles(user_id, req.activo, roles_str)
        if not updated:
            raise NotFoundError("Usuario", str(user_id))
        await self._audit.record(
            correlation_id=correlation_id,
            usuario_id=actor.id,
            username=actor.username,
            entidad="usuario",
            entidad_id=str(user_id),
            operacion="UPDATE",
            resultado="OK",
            fuente="online",
            detalle={"activo": req.activo, "roles": roles_str},
        )
        return updated

    async def _issue_session(
        self, identity: UserIdentity, correlation_id: str, operation: str
    ) -> tuple[AuthTokenResponse, str]:
        access_token = self._tokens.create_access_token(identity)
        raw_refresh, refresh_hash = self._tokens.generate_opaque_token()
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=self._refresh_ttl_days)
        await self._auth.store_refresh_token(identity.id, refresh_hash, expires_at)
        await self._audit.record(
            correlation_id=correlation_id,
            usuario_id=identity.id,
            username=identity.username,
            entidad="usuario",
            entidad_id=str(identity.id),
            operacion=operation,
            resultado="OK",
            fuente="online",
            detalle={"roles": [r.value for r in identity.roles]},
        )
        return (
            AuthTokenResponse(
                access_token=access_token,
                expires_in_seconds=self._access_ttl_minutes * 60,
                offline_grace_until=expires_at,
                user=_to_profile(identity),
            ),
            raw_refresh,
        )
