"""Siembra idempotente inicial de roles, permisos, usuarios y datos de referencia."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import NAMESPACE_DNS, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sajona.application.rbac import ROLE_PERMISSIONS
from sajona.domain.enums import RoleCode
from sajona.infrastructure.models import (
    BajaModel,
    ControlFaseModel,
    CosechaModel,
    ExtraccionMaterialModel,
    FuncionarioModel,
    PermisoModel,
    PermisoRolModel,
    PlantaMadreModel,
    PostCosechaModel,
    PropagacionModel,
    RolModel,
    TipoComplicacionModel,
    TransplanteModel,
    UbicacionModel,
    UsuarioModel,
    UsuarioRolModel,
    VariedadModel,
)
from sajona.infrastructure.security import Argon2PasswordHasher


def _det_uuid(key: str) -> UUID:
    return uuid5(NAMESPACE_DNS, f"sajona.usco.edu.co/{key}")


async def seed_database(session: AsyncSession, include_demo_data: bool = True) -> None:
    """Crea roles, permisos, administrador base y datos iniciales sin duplicar."""
    now = datetime.now(UTC)
    await _seed_roles_and_permissions(session)
    await _seed_users(session, now)
    if include_demo_data:
        await _seed_catalogs(session, now)
        await _seed_sample_lots(session, now)
    await session.commit()


async def _seed_roles_and_permissions(session: AsyncSession) -> None:
    descriptions = {
        RoleCode.ADMIN: "Administrador integral del sistema y seguridad RBAC",
        RoleCode.JEFE_PROYECTO: "Jefe de Proyecto agronómico y trazabilidad",
        RoleCode.OPERARIO: "Operario técnico de invernadero y campo",
        RoleCode.CONSULTA: "Auditor o usuario gerencial de solo lectura",
    }
    all_perms = sorted({p for perms in ROLE_PERMISSIONS.values() for p in perms})
    perm_map: dict[str, UUID] = {}
    for code in all_perms:
        pid = _det_uuid(f"perm/{code}")
        perm_map[code] = pid
        if not await session.get(PermisoModel, pid):
            session.add(
                PermisoModel(id=pid, codigo=code, descripcion=f"Permiso {code}", activo=True)
            )

    for role_code, perms in ROLE_PERMISSIONS.items():
        rid = _det_uuid(f"role/{role_code.value}")
        if not await session.get(RolModel, rid):
            session.add(
                RolModel(
                    id=rid,
                    codigo=role_code.value,
                    descripcion=descriptions[role_code],
                    activo=True,
                )
            )
            await session.flush()
        for perm_code in perms:
            pid = perm_map[perm_code]
            exists = await session.get(PermisoRolModel, (rid, pid))
            if not exists:
                session.add(PermisoRolModel(rol_id=rid, permiso_id=pid))
    await session.flush()


async def _seed_users(session: AsyncSession, now: datetime) -> None:
    hasher = Argon2PasswordHasher()
    accounts = [
        (
            "admin",
            "admin@sajona.co",
            "SajonaAdmin2026!",
            "Carlos",
            "Mendoza",
            "1075200100",
            RoleCode.ADMIN,
        ),
        (
            "jefe",
            "jefe@sajona.co",
            "SajonaJefe2026!",
            "Laura",
            "Quintero",
            "1075200200",
            RoleCode.JEFE_PROYECTO,
        ),
        (
            "operario",
            "operario@sajona.co",
            "SajonaCampo2026!",
            "Andrés",
            "Rojas",
            "1075200300",
            RoleCode.OPERARIO,
        ),
        (
            "consulta",
            "consulta@sajona.co",
            "SajonaAudit2026!",
            "Sofía",
            "Vargas",
            "1075200400",
            RoleCode.CONSULTA,
        ),
    ]
    for uname, email, pwd, nom, ape, doc, role_code in accounts:
        existing = await session.scalar(select(UsuarioModel).where(UsuarioModel.username == uname))
        if existing:
            continue
        fid = _det_uuid(f"func/{uname}")
        uid = _det_uuid(f"user/{uname}")
        session.add(
            FuncionarioModel(
                id=fid,
                nombres=nom,
                apellidos=ape,
                numero_identificacion=doc,
                correo=email,
                telefono="3105550100",
                activo=True,
                version=1,
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            UsuarioModel(
                id=uid,
                funcionario_id=fid,
                username=uname,
                email=email,
                password_hash=hasher.hash(pwd),
                activo=True,
                version=1,
                created_at=now,
                updated_at=now,
            )
        )
        rid = _det_uuid(f"role/{role_code.value}")
        session.add(UsuarioRolModel(usuario_id=uid, rol_id=rid))
    await session.flush()


async def _seed_catalogs(session: AsyncSession, now: datetime) -> None:
    variedades = [
        ("CBD Therapy", "CBD", "Alto contenido de CBD medicinal y bajo THC (<1%)"),
        ("Cannatonic", "BALANCEADA", "Relación equilibrada CBD:THC para extracción"),
        ("Charlotte's Web", "CBD", "Cepa medicinal rica en cannabidiol"),
        ("Harlequin", "CBD", "Híbrida medicinal resistente a plagas"),
    ]
    for nom, perfil, desc in variedades:
        vid = _det_uuid(f"var/{nom}")
        if not await session.get(VariedadModel, vid):
            session.add(
                VariedadModel(
                    id=vid,
                    nombre=nom,
                    perfil=perfil,
                    descripcion=desc,
                    activo=True,
                    version=1,
                    created_at=now,
                    updated_at=now,
                )
            )

    ubicaciones = [
        ("Casa Malla 1", "CASA_MALLA", Decimal("180.00")),
        ("Invernadero Propagación A", "INVERNADERO", Decimal("120.00")),
        ("Área Plantas Madre", "CASA_MALLA", Decimal("90.00")),
        ("Terreno Comercial Norte", "TERRENO", Decimal("1200.00")),
        ("Sala de Secado Principal", "SECADO", Decimal("65.00")),
    ]
    for nom, tipo, cap in ubicaciones:
        uid = _det_uuid(f"ubi/{nom}")
        if not await session.get(UbicacionModel, uid):
            session.add(
                UbicacionModel(
                    id=uid,
                    nombre=nom,
                    tipo=tipo,
                    capacidad_area=cap,
                    activo=True,
                    version=1,
                    created_at=now,
                    updated_at=now,
                )
            )

    complicaciones = [
        ("Marchitamiento", "FITOSANITARIA"),
        ("Botrytis (Moho gris)", "FITOSANITARIA"),
        ("Trips / Ácaros", "PLAGA"),
        ("Deficiencia nutricional", "NUTRICIONAL"),
        ("Estrés hídrico", "AMBIENTAL"),
    ]
    for nom, cat in complicaciones:
        cid = _det_uuid(f"comp/{nom}")
        if not await session.get(TipoComplicacionModel, cid):
            session.add(
                TipoComplicacionModel(
                    id=cid,
                    nombre=nom,
                    categoria=cat,
                    activo=True,
                    version=1,
                    created_at=now,
                    updated_at=now,
                )
            )
    await session.flush()


async def _seed_sample_lots(session: AsyncSession, now: datetime) -> None:
    if await session.scalar(select(PropagacionModel).limit(1)):
        return
    var_cbd = _det_uuid("var/CBD Therapy")
    var_can = _det_uuid("var/Cannatonic")
    ubi_madre = _det_uuid("ubi/Área Plantas Madre")
    ubi_bolsa = _det_uuid("ubi/Casa Malla 1")
    ubi_campo = _det_uuid("ubi/Terreno Comercial Norte")
    comp_mar = _det_uuid("comp/Marchitamiento")
    jefe_id = _det_uuid("user/jefe")

    lote_30 = _det_uuid("lote/30")
    lote_31 = _det_uuid("lote/31")
    session.add_all(
        [
            PropagacionModel(
                id=lote_30,
                codigo_lote="LOT-2026-030",
                fecha_siembra=date(2026, 9, 15),
                tipo_propagacion="ESQUEJE",
                variedad_id=var_cbd,
                tipo_incorporacion="PROPIA",
                cantidad_material=100,
                cantidad_plantas_madre=4,
                observaciones="Lote madre base para clonación continua",
                estado="PLANTA_MADRE",
                created_by=jefe_id,
                version=1,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    await session.flush()
    session.add(
        PropagacionModel(
            id=lote_31,
            codigo_lote="LOT-2026-031",
            fecha_siembra=date(2026, 8, 1),
            tipo_propagacion="ESQUEJE",
            variedad_id=var_can,
            tipo_incorporacion="PROPIA",
            cantidad_material=200,
            cantidad_plantas_madre=0,
            lote_origen_id=lote_30,
            observaciones="Lote comercial derivado de esquejes del lote 30",
            estado="POST_COSECHA",
            created_by=jefe_id,
            version=1,
            created_at=now,
            updated_at=now,
        )
    )
    await session.flush()
    tp_bolsa_30 = _det_uuid("tp/bolsa-30")
    tp_bolsa_31 = _det_uuid("tp/bolsa-31")
    tp_campo_31 = _det_uuid("tp/campo-31")
    session.add_all(
        [
            TransplanteModel(
                id=tp_bolsa_30,
                lote_id=lote_30,
                etapa="BOLSA",
                tipo_lote="PLANTA_MADRE",
                fecha_transplante=date(2026, 10, 1),
                ubicacion_id=ubi_madre,
                cama="M-01",
                cantidad_area=Decimal("45.00"),
                cantidad_buenas=92,
                cantidad_malas=8,
                porcentaje_buenas=Decimal("92.00"),
                porcentaje_malas=Decimal("8.00"),
                estado_transplante="FINALIZADO",
                observaciones="Enraizamiento sobresaliente para madres",
                created_by=jefe_id,
                version=1,
                created_at=now,
                updated_at=now,
            ),
            TransplanteModel(
                id=tp_bolsa_31,
                lote_id=lote_31,
                etapa="BOLSA",
                tipo_lote="PLANTA_COMERCIAL",
                fecha_transplante=date(2026, 8, 18),
                ubicacion_id=ubi_bolsa,
                cama="B-04",
                cantidad_area=Decimal("80.00"),
                cantidad_buenas=184,
                cantidad_malas=16,
                porcentaje_buenas=Decimal("92.00"),
                porcentaje_malas=Decimal("8.00"),
                estado_transplante="FINALIZADO",
                observaciones="Paso a casa malla previo a campo",
                created_by=jefe_id,
                version=1,
                created_at=now,
                updated_at=now,
            ),
            TransplanteModel(
                id=tp_campo_31,
                lote_id=lote_31,
                etapa="CAMPO",
                tipo_lote="PLANTA_COMERCIAL",
                fecha_transplante=date(2026, 9, 2),
                ubicacion_id=ubi_campo,
                cama="Cama 2",
                surco_inicial="S-01",
                surco_final="S-06",
                cantidad_area=Decimal("240.00"),
                cantidad_buenas=180,
                cantidad_malas=4,
                porcentaje_buenas=Decimal("97.83"),
                porcentaje_malas=Decimal("2.17"),
                estado_transplante="FINALIZADO",
                observaciones="Trasplante comercial en terreno norte",
                created_by=jefe_id,
                version=1,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    await session.flush()
    pm15 = _det_uuid("pm/30-15")
    pm16 = _det_uuid("pm/30-16")
    session.add_all(
        [
            PlantaMadreModel(
                id=pm15,
                lote_id=lote_30,
                numero_planta="15",
                fecha_siembra=date(2026, 10, 1),
                ubicacion_id=ubi_madre,
                lugar_siembra="Área Plantas Madre - Hilera A",
                observaciones="Vigor vegetativo óptimo",
                estado="ACTIVA",
                created_by=jefe_id,
                version=1,
                created_at=now,
                updated_at=now,
            ),
            PlantaMadreModel(
                id=pm16,
                lote_id=lote_30,
                numero_planta="16",
                fecha_siembra=date(2026, 10, 1),
                ubicacion_id=ubi_madre,
                lugar_siembra="Área Plantas Madre - Hilera A",
                observaciones="Producción de semilla de reserva",
                estado="ACTIVA",
                created_by=jefe_id,
                version=1,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    await session.flush()
    session.add_all(
        [
            ExtraccionMaterialModel(
                id=_det_uuid("ext/30-15"),
                lote_id=lote_30,
                planta_madre_id=pm15,
                numero_planta_madre="15",
                fecha_extraccion=date(2026, 10, 22),
                fase="ENRAIZAMIENTO",
                cantidad_esquejes=30,
                cantidad_semillas=0,
                observaciones="Corte apical con hormona enraizante",
                created_by=jefe_id,
                version=1,
                created_at=now,
                updated_at=now,
            ),
            ExtraccionMaterialModel(
                id=_det_uuid("ext/30-16"),
                lote_id=lote_30,
                planta_madre_id=pm16,
                numero_planta_madre="16",
                fecha_extraccion=date(2026, 10, 22),
                fase="SIEMBRA_SEMILLA",
                cantidad_esquejes=0,
                cantidad_semillas=20,
                observaciones="Recolección controlada de semillas",
                created_by=jefe_id,
                version=1,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    session.add(
        ControlFaseModel(
            id=_det_uuid("ctrl/31-1"),
            lote_id=lote_31,
            transplante_id=tp_campo_31,
            numero_planta_campo="PC-12",
            fase_cultivo="VEGETATIVA",
            fecha_inicio=date(2026, 9, 5),
            fecha_fin=date(2026, 9, 25),
            tipo_complicacion_id=comp_mar,
            tratamiento_aplicado="Riego foliar preventivo y drenaje en surco S-02",
            estado_revision="BUENA",
            observaciones="Recuperación total tras ajuste hídrico",
            created_by=jefe_id,
            version=1,
            created_at=now,
            updated_at=now,
        )
    )
    cos_31 = _det_uuid("cos/31")
    session.add(
        CosechaModel(
            id=cos_31,
            lote_id=lote_31,
            transplante_campo_id=tp_campo_31,
            fecha_suelo=date(2026, 9, 2),
            fecha_cosecha=date(2026, 11, 2),
            numero_plantas=176,
            cama="Cama 2",
            estado_cosecha="FINALIZADA",
            dias_floracion=61,
            peso_verde=Decimal("48500.00"),
            observaciones="Cosecha en madurez óptima de tricomas",
            created_by=jefe_id,
            version=1,
            created_at=now,
            updated_at=now,
        )
    )
    await session.flush()
    session.add(
        PostCosechaModel(
            id=_det_uuid("post/31"),
            cosecha_id=cos_31,
            lote_id=lote_31,
            fecha_ini_secado=date(2026, 11, 3),
            fecha_fin_secado=date(2026, 11, 14),
            peso_flor_verde=Decimal("42000.00"),
            peso_biomasa=Decimal("6500.00"),
            peso_flor_seco=Decimal("10920.00"),
            porcentaje_cbd=Decimal("14.80"),
            porcentaje_thc=Decimal("0.45"),
            observaciones="Secado controlado a 19°C / 52% HR; certificado de laboratorio",
            created_by=jefe_id,
            version=1,
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        BajaModel(
            id=_det_uuid("baja/31"),
            lote_id=lote_31,
            fecha_baja=date(2026, 9, 10),
            cantidad=4,
            fase_cultivo="CAMPO",
            tipo_complicacion_id=comp_mar,
            observaciones="Descarte preventivo de 4 plantas por marchitamiento severo",
            created_by=jefe_id,
            version=1,
            created_at=now,
            updated_at=now,
        )
    )
