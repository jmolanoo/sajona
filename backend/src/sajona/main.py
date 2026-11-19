"""Punto de entrada de la aplicación FastAPI SAJONA."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from sajona.config import Settings, get_settings
from sajona.domain.exceptions import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from sajona.infrastructure.database import create_engine_and_session
from sajona.infrastructure.models import Base
from sajona.infrastructure.seed import seed_database
from sajona.presentation.routers import (
    admin_router,
    auth_router,
    entities_router,
    health_router,
    sync_router,
)

STATUS_MAP: dict[type[DomainError], int] = {
    ValidationError: 422,
    NotFoundError: 404,
    ConflictError: 409,
    UnauthorizedError: 401,
    ForbiddenError: 403,
}


def _error_payload(code: str, message: str, correlation_id: str) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "correlation_id": correlation_id,
        }
    }


def create_app(custom_settings: Settings | None = None) -> FastAPI:
    """Construye la aplicación FastAPI con middlewares, manejadores y ciclo de vida."""
    settings = custom_settings or get_settings()
    engine, session_factory = create_engine_and_session(settings.database_url)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.engine = engine
        application.state.session_factory = session_factory
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            await seed_database(session, include_demo_data=settings.seed_demo_data)
        yield
        await engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.state.engine = engine
    app.state.session_factory = session_factory

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        cid = request.headers.get("X-Correlation-ID") or str(uuid4())
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        status_code = STATUS_MAP.get(type(exc), 400)
        cid = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(
            status_code=status_code,
            content=_error_payload(exc.code, exc.message, cid),
        )

    @app.exception_handler(PydanticValidationError)
    async def handle_pydantic_error(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        cid = getattr(request.state, "correlation_id", "unknown")
        errors = exc.errors()
        if errors:
            first = errors[0]
            loc = ".".join(str(x) for x in first.get("loc", ()))
            msg = f"{loc}: {first.get('msg')}" if loc else str(first.get("msg"))
        else:
            msg = "Datos inválidos"
        return JSONResponse(
            status_code=422,
            content=_error_payload("VALIDATION_ERROR", msg, cid),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException) -> JSONResponse:
        cid = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(f"HTTP_{exc.status_code}", str(exc.detail), cid),
        )

    for router in (health_router, auth_router, admin_router, entities_router, sync_router):
        app.include_router(router)

    return app


app = create_app()
