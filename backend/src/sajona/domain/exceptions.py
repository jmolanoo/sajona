"""Excepciones de dominio independientes de infraestructura o HTTP."""


class DomainError(Exception):
    """Error base de reglas de negocio o dominio."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class ValidationError(DomainError):
    """Violación de invariantes o validaciones de negocio."""

    def __init__(self, message: str, code: str = "DOMAIN_VALIDATION_ERROR") -> None:
        super().__init__(code=code, message=message)


class NotFoundError(DomainError):
    """Recurso de dominio no encontrado."""

    def __init__(self, entity: str, identifier: str) -> None:
        super().__init__(
            code="NOT_FOUND",
            message=f"{entity} con identificador '{identifier}' no existe.",
        )


class ConflictError(DomainError):
    """Conflicto de versión optimista o unicidad."""

    def __init__(self, message: str, code: str = "VERSION_CONFLICT") -> None:
        super().__init__(code=code, message=message)


class UnauthorizedError(DomainError):
    """Credenciales inválidas o sesión expirada."""

    def __init__(self, message: str = "No autenticado o token inválido.") -> None:
        super().__init__(code="UNAUTHORIZED", message=message)


class ForbiddenError(DomainError):
    """Usuario autenticado sin permisos para la operación."""

    def __init__(self, message: str = "No posee permisos para ejecutar esta acción.") -> None:
        super().__init__(code="FORBIDDEN", message=message)
