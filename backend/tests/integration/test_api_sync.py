"""Pruebas de integración de API, RBAC, auditoría, idempotencia y conflictos de sincronización."""

from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sajona.config import Settings
from sajona.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    db_file = tmp_path / "test_sajona.db"
    audit_dir = tmp_path / "audit"
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_file}",
        jwt_secret_key="test-secret-key-sajona-32-chars-minimum",
        audit_log_dir=str(audit_dir),
        seed_demo_data=True,
        cookie_secure=False,
    )
    app = create_app(settings)
    with TestClient(app) as tc:
        yield tc


def _login(client: TestClient, identifier: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert resp.status_code == 200, resp.text
    return str(resp.json()["access_token"])


def test_ac01_health_y_openapi_contract(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert "X-Correlation-ID" in health.headers

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    assert "/api/v1/sync/push" in paths
    assert "/api/v1/sync/pull" in paths


def test_ac02_autenticacion_refresh_logout_y_admin_usuarios(client: TestClient) -> None:
    consulta_token = _login(client, "consulta", "SajonaAudit2026!")
    denied = client.post(
        "/api/v1/entities/variedad",
        headers={"Authorization": f"Bearer {consulta_token}"},
        json={"nombre": "NoPermitida", "perfil": "CBD"},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN"

    # Refresh token rotation via cookie
    refresh_resp = client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    new_consulta_token = refresh_resp.json()["access_token"]
    me_resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {new_consulta_token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "consulta"

    logout_resp = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {new_consulta_token}"}
    )
    assert logout_resp.status_code == 200
    assert client.post("/api/v1/auth/refresh").status_code == 401

    # Admin users & roles
    admin_token = _login(client, "admin", "SajonaAdmin2026!")
    ah = {"Authorization": f"Bearer {admin_token}"}
    assert client.get("/api/v1/admin/roles", headers=ah).status_code == 200
    assert len(client.get("/api/v1/admin/users", headers=ah).json()) >= 4

    created_u = client.post(
        "/api/v1/admin/users",
        headers=ah,
        json={
            "username": "nuevo_op",
            "email": "nuevo_op@sajona.co",
            "password": "Password2026!",
            "nombres": "Mateo",
            "apellidos": "Silva",
            "numero_identificacion": "1075999888",
            "telefono": "3112223344",
            "roles": ["OPERARIO"],
        },
    )
    assert created_u.status_code == 201
    uid = created_u.json()["id"]
    upd_u = client.patch(
        f"/api/v1/admin/users/{uid}",
        headers=ah,
        json={"activo": False, "roles": ["CONSULTA"]},
    )
    assert upd_u.status_code == 200
    assert upd_u.json()["activo"] is False

    # Password reset
    reset_req = client.post(
        "/api/v1/auth/password-reset/request",
        json={"identifier": "operario@sajona.co"},
    )
    assert reset_req.status_code == 200
    token = reset_req.json()["reset_token_preview"]
    reset_confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "NuevoPassword2026!"},
    )
    assert reset_confirm.status_code == 200
    assert len(_login(client, "operario", "NuevoPassword2026!")) > 20


def test_ac03_ciclo_completo_todas_entidades_y_auditoria(client: TestClient) -> None:
    admin_token = _login(client, "admin", "SajonaAdmin2026!")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Crear catálogos nuevos
    v_resp = client.post(
        "/api/v1/entities/variedad",
        headers=headers,
        json={"nombre": "ACDC Medicinal", "perfil": "CBD", "descripcion": "Alta pureza CBD"},
    )
    assert v_resp.status_code == 201
    var_id = v_resp.json()["id"]

    u_resp = client.post(
        "/api/v1/entities/ubicacion",
        headers=headers,
        json={"nombre": "Casa Malla Sur", "tipo": "CASA_MALLA", "capacidad_area": 150},
    )
    assert u_resp.status_code == 201
    ubi_id = u_resp.json()["id"]

    c_resp = client.post(
        "/api/v1/entities/tipo_complicacion",
        headers=headers,
        json={"nombre": "Oídio", "categoria": "FITOSANITARIA"},
    )
    assert c_resp.status_code == 201
    comp_id = c_resp.json()["id"]

    # Propagación -> Bolsa -> Planta Madre -> Extracción -> Control Fase -> Cosecha -> Post -> Baja
    lote_resp = client.post(
        "/api/v1/entities/propagacion",
        headers=headers,
        json={
            "codigo_lote": "LOT-TEST-500",
            "fecha_siembra": "2026-11-01",
            "tipo_propagacion": "ESQUEJE",
            "variedad_id": var_id,
            "tipo_incorporacion": "PROPIA",
            "cantidad_material": 80,
            "cantidad_plantas_madre": 2,
        },
    )
    assert lote_resp.status_code == 201
    lote_id = lote_resp.json()["id"]

    tp_resp = client.post(
        "/api/v1/entities/transplante",
        headers=headers,
        json={
            "lote_id": lote_id,
            "etapa": "BOLSA",
            "tipo_lote": "PLANTA_MADRE",
            "fecha_transplante": "2026-11-10",
            "ubicacion_id": ubi_id,
            "cantidad_area": 30,
            "cantidad_buenas": 72,
            "estado_transplante": "FINALIZADO",
        },
    )
    assert tp_resp.status_code == 201
    assert tp_resp.json()["cantidad_malas"] == 8

    pm_resp = client.post(
        "/api/v1/entities/planta_madre",
        headers=headers,
        json={
            "lote_id": lote_id,
            "numero_planta": "PM-01",
            "fecha_siembra": "2026-11-10",
            "ubicacion_id": ubi_id,
            "lugar_siembra": "Mesa 1",
        },
    )
    assert pm_resp.status_code == 201
    pm_id = pm_resp.json()["id"]

    ext_resp = client.post(
        "/api/v1/entities/extraccion_material",
        headers=headers,
        json={
            "lote_id": lote_id,
            "planta_madre_id": pm_id,
            "numero_planta_madre": "PM-01",
            "fecha_extraccion": "2026-11-12",
            "fase": "ENRAIZAMIENTO",
            "cantidad_esquejes": 25,
            "cantidad_semillas": 0,
        },
    )
    assert ext_resp.status_code == 201

    ctrl_resp = client.post(
        "/api/v1/entities/control_fase",
        headers=headers,
        json={
            "lote_id": lote_id,
            "numero_planta_campo": "PC-05",
            "fase_cultivo": "VEGETATIVA",
            "fecha_inicio": "2026-11-12",
            "tipo_complicacion_id": comp_id,
            "tratamiento_aplicado": "Biocontrolador foliar",
            "estado_revision": "EN_TRATAMIENTO",
        },
    )
    assert ctrl_resp.status_code == 201

    cos_resp = client.post(
        "/api/v1/entities/cosecha",
        headers=headers,
        json={
            "lote_id": lote_id,
            "fecha_suelo": "2026-10-01",
            "fecha_cosecha": "2026-11-15",
            "numero_plantas": 70,
            "cama": "C-08",
            "estado_cosecha": "FINALIZADA",
            "peso_verde": 15000,
        },
    )
    assert cos_resp.status_code == 201
    cos_id = cos_resp.json()["id"]

    post_resp = client.post(
        "/api/v1/entities/post_cosecha",
        headers=headers,
        json={
            "cosecha_id": cos_id,
            "lote_id": lote_id,
            "fecha_ini_secado": "2026-11-16",
            "fecha_fin_secado": "2026-11-18",
            "peso_flor_verde": 12000,
            "peso_biomasa": 3000,
            "peso_flor_seco": 3100,
            "porcentaje_cbd": 16.75,
            "porcentaje_thc": 0.48,
        },
    )
    assert post_resp.status_code == 201
    assert post_resp.json()["porcentaje_cbd"] == 16.75

    baja_resp = client.post(
        "/api/v1/entities/baja",
        headers=headers,
        json={
            "lote_id": lote_id,
            "fecha_baja": "2026-11-14",
            "cantidad": 5,
            "fase_cultivo": "VEGETATIVA",
            "tipo_complicacion_id": comp_id,
            "observaciones": "Descarte por oídio",
        },
    )
    assert baja_resp.status_code == 201
    baja_id = baja_resp.json()["id"]

    trace = client.get(f"/api/v1/entities/lotes/{lote_id}/trazabilidad", headers=headers)
    assert trace.status_code == 200
    assert trace.json()["resumen"]["saldo_vivo"] == 75

    # Soft delete + verificación de exclusión en listado
    del_resp = client.delete(f"/api/v1/entities/baja/{baja_id}", headers=headers)
    assert del_resp.status_code == 200
    assert client.get(f"/api/v1/entities/baja?lote_id={lote_id}", headers=headers).json() == []

    logs = client.get("/api/v1/admin/audit-logs?entidad=post_cosecha", headers=headers)
    assert logs.status_code == 200
    assert len(logs.json()) >= 1


def test_ac04_offline_sync_idempotencia_conflictos_y_rechazos(client: TestClient) -> None:
    jefe_token = _login(client, "jefe", "SajonaJefe2026!")
    headers = {"Authorization": f"Bearer {jefe_token}"}

    variedades = client.get("/api/v1/entities/variedad", headers=headers).json()
    var_id = variedades[0]["id"]
    lote_id = str(uuid4())
    mut_create_id = str(uuid4())

    push_payload = {
        "client_device_id": "mobile-field-01",
        "mutations": [
            {
                "client_mutation_id": mut_create_id,
                "entity_type": "propagacion",
                "entity_id": lote_id,
                "operation": "CREATE",
                "base_version": 0,
                "payload": {
                    "codigo_lote": "LOT-OFFLINE-99",
                    "fecha_siembra": "2026-11-12",
                    "tipo_propagacion": "SEMILLA",
                    "variedad_id": var_id,
                    "tipo_incorporacion": "COMPRADA",
                    "cantidad_material": 60,
                    "cantidad_plantas_madre": 0,
                    "observaciones": "Creado sin señal en campo",
                },
            }
        ],
    }
    first_push = client.post("/api/v1/sync/push", headers=headers, json=push_payload)
    assert first_push.status_code == 200
    assert first_push.json()["results"][0]["status"] == "applied"
    assert first_push.json()["results"][0]["new_version"] == 1

    # Reintento con mismo client_mutation_id -> duplicate
    retry_push = client.post("/api/v1/sync/push", headers=headers, json=push_payload)
    assert retry_push.status_code == 200
    assert retry_push.json()["results"][0]["status"] == "duplicate"

    # Actualización concurrente en servidor sube versión a 2
    upd_online = client.put(
        f"/api/v1/entities/propagacion/{lote_id}",
        headers={**headers, "X-Expected-Version": "1"},
        json={
            "codigo_lote": "LOT-OFFLINE-99",
            "fecha_siembra": "2026-11-12",
            "tipo_propagacion": "SEMILLA",
            "variedad_id": var_id,
            "tipo_incorporacion": "COMPRADA",
            "cantidad_material": 65,
            "cantidad_plantas_madre": 0,
            "observaciones": "Ajustado en oficina",
        },
    )
    assert upd_online.status_code == 200
    assert upd_online.json()["version"] == 2

    # Otro dispositivo offline intenta editar con base_version=1 -> conflict
    conflict_push = client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "client_device_id": "mobile-field-02",
            "mutations": [
                {
                    "client_mutation_id": str(uuid4()),
                    "entity_type": "propagacion",
                    "entity_id": lote_id,
                    "operation": "UPDATE",
                    "base_version": 1,
                    "payload": {
                        "codigo_lote": "LOT-OFFLINE-99",
                        "fecha_siembra": "2026-11-12",
                        "tipo_propagacion": "SEMILLA",
                        "variedad_id": var_id,
                        "tipo_incorporacion": "COMPRADA",
                        "cantidad_material": 58,
                        "cantidad_plantas_madre": 0,
                        "observaciones": "Cambio concurrente en campo",
                    },
                }
            ],
        },
    )
    assert conflict_push.status_code == 200
    outcome = conflict_push.json()["results"][0]
    assert outcome["status"] == "conflict"
    assert outcome["new_version"] == 2
    assert outcome["server_record"]["cantidad_material"] == 65

    # Sync DELETE con versión vigente 2 -> applied
    del_push = client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "client_device_id": "mobile-field-02",
            "mutations": [
                {
                    "client_mutation_id": str(uuid4()),
                    "entity_type": "propagacion",
                    "entity_id": lote_id,
                    "operation": "DELETE",
                    "base_version": 2,
                    "payload": {},
                }
            ],
        },
    )
    assert del_push.status_code == 200
    assert del_push.json()["results"][0]["status"] == "applied"
    assert del_push.json()["results"][0]["new_version"] == 3

    # Pull incremental refleja versión 3 con deleted_at != None
    pull_resp = client.get("/api/v1/sync/pull?since=2020-01-01T00:00:00Z", headers=headers)
    assert pull_resp.status_code == 200
    lotes = pull_resp.json()["changes"]["propagacion"]
    assert any(
        item["id"] == lote_id and item["version"] == 3 and item["deleted_at"] is not None
        for item in lotes
    )
