"""Enumeraciones y constantes de dominio para SAJONA."""

from enum import StrEnum


class RoleCode(StrEnum):
    """Roles RBAC oficiales del sistema."""

    ADMIN = "ADMIN"
    JEFE_PROYECTO = "JEFE_PROYECTO"
    OPERARIO = "OPERARIO"
    CONSULTA = "CONSULTA"


class TipoPropagacion(StrEnum):
    """Método inicial de propagación del lote."""

    ESQUEJE = "ESQUEJE"
    SEMILLA = "SEMILLA"
    IN_VITRO = "IN_VITRO"


class TipoIncorporacion(StrEnum):
    """Origen de incorporación del material vegetal."""

    PROPIA = "PROPIA"
    COMPRADA = "COMPRADA"


class EstadoLote(StrEnum):
    """Ciclo de vida macro de un lote trazable."""

    PROPAGACION = "PROPAGACION"
    TRANSPLANTE_BOLSA = "TRANSPLANTE_BOLSA"
    PLANTA_MADRE = "PLANTA_MADRE"
    TRANSPLANTE_CAMPO = "TRANSPLANTE_CAMPO"
    COSECHA = "COSECHA"
    POST_COSECHA = "POST_COSECHA"
    FINALIZADO = "FINALIZADO"


class EtapaTransplante(StrEnum):
    """Etapa de trasplante."""

    BOLSA = "BOLSA"
    CAMPO = "CAMPO"


class TipoLoteTransplante(StrEnum):
    """Destino productivo del lote al trasplantarse."""

    PLANTA_MADRE = "PLANTA_MADRE"
    PLANTA_COMERCIAL = "PLANTA_COMERCIAL"


class EstadoTransplante(StrEnum):
    """Estado operativo del trasplante."""

    TRANSPLANTE = "TRANSPLANTE"
    FINALIZADO = "FINALIZADO"


class FaseCultivo(StrEnum):
    """Fases fenológicas y operativas de seguimiento y bajas."""

    PROPAGACION = "PROPAGACION"
    CUBICULO = "CUBICULO"
    ENRAIZAMIENTO = "ENRAIZAMIENTO"
    BOLSA = "BOLSA"
    PLANTA_MADRE = "PLANTA_MADRE"
    CAMPO = "CAMPO"
    VEGETATIVA = "VEGETATIVA"
    FLORACION = "FLORACION"
    COSECHA = "COSECHA"
    POST_COSECHA = "POST_COSECHA"
    ALMACENAMIENTO = "ALMACENAMIENTO"
    SIEMBRA_SEMILLA = "SIEMBRA_SEMILLA"


class EstadoRevision(StrEnum):
    """Estado sanitario en control o revisión."""

    BUENA = "BUENA"
    MALA = "MALA"
    EN_TRATAMIENTO = "EN_TRATAMIENTO"
    DESCARTADA = "DESCARTADA"


class EstadoCosecha(StrEnum):
    """Estado del registro de cosecha."""

    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    FINALIZADA = "FINALIZADA"


class TipoUbicacion(StrEnum):
    """Clasificación de ubicaciones productivas."""

    CASA_MALLA = "CASA_MALLA"
    INVERNADERO = "INVERNADERO"
    TERRENO = "TERRENO"
    SECADO = "SECADO"
    OTRO = "OTRO"


class PerfilVariedad(StrEnum):
    """Perfil predominante de cannabinoides de la variedad."""

    CBD = "CBD"
    THC = "THC"
    BALANCEADA = "BALANCEADA"
