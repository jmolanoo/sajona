"""Políticas centralizadas de Control de Acceso Basado en Roles (RBAC)."""

from sajona.domain.entities import UserIdentity
from sajona.domain.enums import RoleCode
from sajona.domain.exceptions import ForbiddenError

ROLE_PERMISSIONS: dict[RoleCode, list[str]] = {
    RoleCode.ADMIN: [
        "users:read",
        "users:write",
        "audit:read",
        "catalogs:read",
        "catalogs:write",
        "production:read",
        "production:write",
        "production:delete",
        "reports:read",
        "sync:execute",
    ],
    RoleCode.JEFE_PROYECTO: [
        "audit:read",
        "catalogs:read",
        "catalogs:write",
        "production:read",
        "production:write",
        "production:delete",
        "reports:read",
        "sync:execute",
    ],
    RoleCode.OPERARIO: [
        "catalogs:read",
        "production:read",
        "production:write",
        "reports:read",
        "sync:execute",
    ],
    RoleCode.CONSULTA: [
        "catalogs:read",
        "production:read",
        "reports:read",
    ],
}


def resolve_permissions(roles: list[RoleCode]) -> list[str]:
    """Agrega permisos únicos correspondientes a una lista de roles."""
    perms: set[str] = set()
    for role in roles:
        perms.update(ROLE_PERMISSIONS.get(role, []))
    return sorted(perms)


def require_permission(identity: UserIdentity, permission: str) -> None:
    """Exige que el usuario autenticado posea el permiso requerido."""
    if not identity.activo:
        raise ForbiddenError("La cuenta de usuario se encuentra inactiva.")
    if permission not in identity.permissions:
        raise ForbiddenError(f"Se requiere el permiso '{permission}' para esta acción.")


def permission_for_entity_operation(entity_type: str, operation: str) -> str:
    """Determina el permiso necesario para operar sobre un tipo de entidad."""
    is_catalog = entity_type in {"variedad", "ubicacion", "tipo_complicacion"}
    if operation == "DELETE":
        return "catalogs:write" if is_catalog else "production:delete"
    return "catalogs:write" if is_catalog else "production:write"
