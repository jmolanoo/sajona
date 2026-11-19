"""Pruebas de casos borde, errores uniformes, filtros por fecha y cobertura de aplicación."""

from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sajona.config import Settings
from sajona.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    db_file = tmp_path / "test_edge.db"
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_file}",
        jwt_secret_key="test-secret-key-sajona-32-chars-minimum",
        audit_log_dir=str(tmp_path / "audit"),
        seed_demo_data=True,
        cookie_secure=False,
    )
    app = create_app(settings)
    with TestClient(app) as tc:
        yield tc


def test_ac05_errores_uniformes_filtros_y_edge_cases(client: TestClient) -> None:
    # Login fallido devuelve 401 con formato uniforme
    bad_login = client.post(
        "/api/v1/auth/login", json={"identifier": "admin", "password": "wrong-password"}
    )
    assert bad_login.status_code == 401
    assert bad_login.json()["error"]["code"] == "UNAUTHORIZED"

    # Acceso sin token -> 401
    assert client.get("/api/v1/auth/me").status_code == 401

    # Reset con token inválido -> 422
    bad_reset = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "invalid-reset-token-123456", "new_password": "Password2026!"},
    )
    assert bad_reset.status_code == 422

    # Login admin exitoso
    tok = client.post(
        "/api/v1/auth/login", json={"identifier": "admin", "password": "SajonaAdmin2026!"}
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    # Usuario duplicado -> 409
    dup_u = client.post(
        "/api/v1/admin/users",
        headers=h,
        json={
            "username": "admin",
            "email": "otro@sajona.co",
            "password": "Password2026!",
            "nombres": "Dup",
            "apellidos": "Test",
            "numero_identificacion": "999888777",
            "telefono": "3001112233",
            "roles": ["ADMIN"],
        },
    )
    assert dup_u.status_code == 409

    # Filtros por fecha en propagacion
    lotes = client.get(
        "/api/v1/entities/propagacion?fecha_inicio=2026-01-01&fecha_fin=2026-12-31",
        headers=h,
    ).json()
    assert len(lotes) >= 2
    lote = lotes[0]

    # Conflicto de versión en PUT online
    bad_put = client.put(
        f"/api/v1/entities/propagacion/{lote['id']}",
        headers={**h, "X-Expected-Version": "999"},
        json=lote,
    )
    assert bad_put.status_code == 409

    # Sync con entidad desconocida -> rejected; update a entidad inexistente -> rejected;
    # create duplicado -> conflict
    sync_edges = client.post(
        "/api/v1/sync/push",
        headers=h,
        json={
            "client_device_id": "edge-test",
            "mutations": [
                {
                    "client_mutation_id": str(uuid4()),
                    "entity_type": "desconocida",
                    "entity_id": str(uuid4()),
                    "operation": "CREATE",
                    "base_version": 0,
                    "payload": {},
                },
                {
                    "client_mutation_id": str(uuid4()),
                    "entity_type": "propagacion",
                    "entity_id": str(uuid4()),
                    "operation": "UPDATE",
                    "base_version": 1,
                    "payload": {},
                },
                {
                    "client_mutation_id": str(uuid4()),
                    "entity_type": "propagacion",
                    "entity_id": lote["id"],
                    "operation": "CREATE",
                    "base_version": 0,
                    "payload": lote,
                },
            ],
        },
    )
    assert sync_edges.status_code == 200
    statuses = [r["status"] for r in sync_edges.json()["results"]]
    assert statuses == ["rejected", "rejected", "conflict"]

    # Traza de lote inexistente -> 404
    missing_trace = client.get(f"/api/v1/entities/lotes/{uuid4()}/trazabilidad", headers=h)
    assert missing_trace.status_code == 404
