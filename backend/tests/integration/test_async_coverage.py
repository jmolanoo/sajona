"""Pruebas asíncronas directas ASGI para medición exacta de cobertura y casos límite."""

from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from sajona.config import Settings
from sajona.infrastructure.database import create_engine_and_session
from sajona.infrastructure.models import Base
from sajona.infrastructure.seed import seed_database
from sajona.main import create_app


@pytest.fixture()
async def async_client(tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    db_file = tmp_path / "async_sajona.db"
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_file}",
        jwt_secret_key="test-secret-key-sajona-32-chars-minimum",
        audit_log_dir=str(tmp_path / "audit"),
        seed_demo_data=True,
        cookie_secure=False,
    )
    engine, session_factory = create_engine_and_session(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        await seed_database(session, include_demo_data=True)
    await engine.dispose()

    app = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


async def test_ac06_flujo_asincrono_completo_y_errores(async_client: httpx.AsyncClient) -> None:
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@sajona.co", "password": "SajonaAdmin2026!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Actualizar lote existente + validar refresh + consultar auditoría
    lotes = (await async_client.get("/api/v1/entities/propagacion", headers=headers)).json()
    lote = lotes[0]
    upd = await async_client.put(
        f"/api/v1/entities/propagacion/{lote['id']}",
        headers=headers,
        json={**lote, "observaciones": "Actualizado en prueba asíncrona"},
    )
    assert upd.status_code == 200
    assert upd.json()["version"] == lote["version"] + 1

    # Sync UPDATE exitoso y Sync PULL incremental
    push = await async_client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "client_device_id": "async-test",
            "mutations": [
                {
                    "client_mutation_id": str(uuid4()),
                    "entity_type": "propagacion",
                    "entity_id": lote["id"],
                    "operation": "UPDATE",
                    "base_version": upd.json()["version"],
                    "payload": {**lote, "observaciones": "Actualizado vía sync"},
                }
            ],
        },
    )
    assert push.status_code == 200
    assert push.json()["results"][0]["status"] == "applied"

    pull = await async_client.get("/api/v1/sync/pull", headers=headers)
    assert pull.status_code == 200
    assert len(pull.json()["changes"]["variedad"]) >= 4

    # Auditoría filtrada por usuario
    audit = await async_client.get("/api/v1/admin/audit-logs?usuario=admin", headers=headers)
    assert audit.status_code == 200
    assert len(audit.json()) >= 2

    # Logout + verificación de cookie revocada
    assert (await async_client.post("/api/v1/auth/logout", headers=headers)).status_code == 200
    assert (await async_client.post("/api/v1/auth/refresh")).status_code == 401
