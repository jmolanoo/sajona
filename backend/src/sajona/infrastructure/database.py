"""Configuración de motor SQLAlchemy 2 asíncrono y sesiones."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine_and_session(
    database_url: str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Construye motor asíncrono y fábrica de sesiones para PostgreSQL o SQLite."""
    kwargs: dict[str, object] = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}
    engine = create_async_engine(database_url, **kwargs)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, session_factory


async def yield_session(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Generador de sesión transaccional por solicitud."""
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
