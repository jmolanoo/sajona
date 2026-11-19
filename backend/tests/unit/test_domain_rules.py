"""Pruebas unitarias de reglas de dominio puras (RN-01 a RN-06)."""

from datetime import date
from decimal import Decimal

import pytest

from sajona.domain.exceptions import ValidationError
from sajona.domain.rules import (
    calcular_dias_floracion,
    calcular_resumen_secado,
    calcular_supervivencia_transplante,
    validar_baja_contra_saldo,
    validar_porcentaje_cannabinoide,
    validar_rango_fechas_fase,
)


def test_rn02_calcular_supervivencia_transplante_calcula_merma_y_alerta() -> None:
    res = calcular_supervivencia_transplante(100, 75)
    assert res.cantidad_buenas == 75
    assert res.cantidad_malas == 25
    assert res.porcentaje_buenas == Decimal("75.00")
    assert res.porcentaje_malas == Decimal("25.00")
    assert res.requiere_alerta_merma is True


def test_rn02_calcular_supervivencia_rechaza_buenas_mayores_a_disponible() -> None:
    with pytest.raises(ValidationError):
        calcular_supervivencia_transplante(50, 51)


def test_rn02_calcular_supervivencia_rechaza_disponible_cero_o_negativo() -> None:
    with pytest.raises(ValidationError):
        calcular_supervivencia_transplante(0, 0)
    with pytest.raises(ValidationError):
        calcular_supervivencia_transplante(20, -1)


def test_rn02_validar_baja_contra_saldo_actualiza_y_protege_inventario() -> None:
    restante = validar_baja_contra_saldo(100, 15, 10)
    assert restante == 75
    with pytest.raises(ValidationError):
        validar_baja_contra_saldo(100, 90, 15)
    with pytest.raises(ValidationError):
        validar_baja_contra_saldo(100, 0, 0)


def test_rn05_validar_porcentaje_cannabinoide_acepta_valores_reales_decimal_5_2() -> None:
    assert validar_porcentaje_cannabinoide("CBD", Decimal("18.456")) == Decimal("18.46")
    assert validar_porcentaje_cannabinoide("THC", Decimal("0.45")) == Decimal("0.45")
    with pytest.raises(ValidationError):
        validar_porcentaje_cannabinoide("CBD", Decimal("100.01"))
    with pytest.raises(ValidationError):
        validar_porcentaje_cannabinoide("THC", Decimal("-0.10"))


def test_rn04_calcular_resumen_secado_y_validacion_pesos_fechas() -> None:
    res = calcular_resumen_secado(
        Decimal("1000.00"),
        Decimal("200.00"),
        Decimal("250.00"),
        date(2026, 11, 1),
        date(2026, 11, 10),
    )
    assert res.rendimiento_secado_pct == Decimal("25.00")
    assert res.merma_secado_pct == Decimal("75.00")

    with pytest.raises(ValidationError):
        calcular_resumen_secado(
            Decimal("100"), Decimal("0"), Decimal("120"), date(2026, 11, 1), None
        )
    with pytest.raises(ValidationError):
        calcular_resumen_secado(
            Decimal("100"), Decimal("0"), Decimal("20"), date(2026, 11, 10), date(2026, 11, 2)
        )


def test_rn04_dias_floracion_y_rango_fechas_fase() -> None:
    assert calcular_dias_floracion(date(2026, 9, 1), date(2026, 11, 1)) == 61
    with pytest.raises(ValidationError):
        calcular_dias_floracion(date(2026, 11, 1), date(2026, 10, 1))
    validar_rango_fechas_fase(date(2026, 9, 1), date(2026, 9, 20), None)
    with pytest.raises(ValidationError):
        validar_rango_fechas_fase(date(2026, 9, 10), date(2026, 9, 1), None)
    with pytest.raises(ValidationError):
        validar_rango_fechas_fase(date(2026, 9, 10), None, date(2026, 9, 5))
