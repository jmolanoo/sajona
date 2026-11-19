"""Reglas y cálculos agronómicos puros del dominio SAJONA."""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sajona.domain.exceptions import ValidationError

HUNDRED = Decimal("100.00")
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class ResultadoSupervivencia:
    """Resultado calculado de supervivencia y merma en trasplante."""

    cantidad_disponible: int
    cantidad_buenas: int
    cantidad_malas: int
    porcentaje_buenas: Decimal
    porcentaje_malas: Decimal
    requiere_alerta_merma: bool


@dataclass(frozen=True)
class ResumenPostCosecha:
    """Métricas de rendimiento de secado y validación química."""

    peso_flor_verde: Decimal
    peso_biomasa: Decimal
    peso_flor_seco: Decimal
    rendimiento_secado_pct: Decimal
    merma_secado_pct: Decimal


def calcular_supervivencia_transplante(
    cantidad_disponible: int,
    cantidad_buenas: int,
    umbral_alerta_malas_pct: Decimal = Decimal("20.00"),
) -> ResultadoSupervivencia:
    """Calcula unidades malas y porcentajes exactos validando balance biológico."""
    if cantidad_disponible <= 0:
        raise ValidationError("La cantidad disponible del lote debe ser mayor a cero.")
    if cantidad_buenas < 0:
        raise ValidationError("La cantidad de unidades buenas no puede ser negativa.")
    if cantidad_buenas > cantidad_disponible:
        raise ValidationError(
            f"Las unidades buenas ({cantidad_buenas}) superan el saldo disponible "
            f"({cantidad_disponible})."
        )

    cantidad_malas = cantidad_disponible - cantidad_buenas
    total_dec = Decimal(cantidad_disponible)
    pct_buenas = ((Decimal(cantidad_buenas) * HUNDRED) / total_dec).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    pct_malas = (HUNDRED - pct_buenas).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return ResultadoSupervivencia(
        cantidad_disponible=cantidad_disponible,
        cantidad_buenas=cantidad_buenas,
        cantidad_malas=cantidad_malas,
        porcentaje_buenas=pct_buenas,
        porcentaje_malas=pct_malas,
        requiere_alerta_merma=pct_malas > umbral_alerta_malas_pct,
    )


def validar_baja_contra_saldo(
    cantidad_inicial: int,
    bajas_previas: int,
    nueva_baja: int,
) -> int:
    """Verifica que las bajas acumuladas no superen el inventario inicial del lote."""
    if nueva_baja <= 0:
        raise ValidationError("La cantidad de bajas debe ser mayor a cero.")
    saldo_actual = cantidad_inicial - bajas_previas
    if nueva_baja > saldo_actual:
        raise ValidationError(
            f"La baja ({nueva_baja}) supera el saldo vivo disponible del lote ({saldo_actual})."
        )
    return saldo_actual - nueva_baja


def validar_porcentaje_cannabinoide(nombre: str, valor: Decimal) -> Decimal:
    """Valida rangos químicos reales (0.00% a 100.00%) en DECIMAL(5,2)."""
    if valor < ZERO or valor > HUNDRED:
        raise ValidationError(
            f"El porcentaje de {nombre} ({valor}%) debe estar entre 0.00 y 100.00."
        )
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_resumen_secado(
    peso_flor_verde: Decimal,
    peso_biomasa: Decimal,
    peso_flor_seco: Decimal,
    fecha_inicio: date,
    fecha_fin: date | None,
) -> ResumenPostCosecha:
    """Valida consistencia de pesos y fechas en postcosecha y calcula rendimiento."""
    if peso_flor_verde <= Decimal("0"):
        raise ValidationError("El peso de flor verde debe ser mayor a cero.")
    if peso_biomasa < Decimal("0") or peso_flor_seco < Decimal("0"):
        raise ValidationError("Los pesos de biomasa y flor seca no pueden ser negativos.")
    if peso_flor_seco > peso_flor_verde:
        raise ValidationError(
            "El peso de flor seca no puede superar el peso de flor verde inicial."
        )
    if fecha_fin is not None and fecha_fin < fecha_inicio:
        raise ValidationError(
            "La fecha de fin de secado no puede ser anterior a la fecha de inicio."
        )

    rendimiento = ((peso_flor_seco * HUNDRED) / peso_flor_verde).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    merma = (HUNDRED - rendimiento).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return ResumenPostCosecha(
        peso_flor_verde=peso_flor_verde.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        peso_biomasa=peso_biomasa.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        peso_flor_seco=peso_flor_seco.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        rendimiento_secado_pct=rendimiento,
        merma_secado_pct=merma,
    )


def calcular_dias_floracion(fecha_suelo: date, fecha_cosecha: date) -> int:
    """Calcula días transcurridos entre trasplante en campo y cosecha."""
    if fecha_cosecha < fecha_suelo:
        raise ValidationError(
            "La fecha de cosecha no puede ser anterior a la fecha en campo."
        )
    return (fecha_cosecha - fecha_suelo).days


def validar_rango_fechas_fase(
    fecha_inicio: date,
    fecha_fin: date | None,
    fecha_descarte: date | None,
) -> None:
    """Valida coherencia cronológica de controles de fase fenológica."""
    if fecha_fin is not None and fecha_fin < fecha_inicio:
        raise ValidationError("La fecha final de fase no puede ser anterior al inicio.")
    if fecha_descarte is not None and fecha_descarte < fecha_inicio:
        raise ValidationError("La fecha de descarte no puede ser anterior al inicio de fase.")
