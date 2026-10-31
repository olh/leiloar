"""Tests for judicial auction edital parsing."""

from pathlib import Path
from leiloar.parsers.edital_parser import JudicialEditalParser


def test_parse_sample_edital_judicial():
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "sample_edital_judicial.txt"
    with open(fixture_path, "r", encoding="utf-8") as f:
        text = f.read()

    parser = JudicialEditalParser()
    result = parser.parse(text)

    # CNJ & Court
    assert result.cnj_number == "1014522-74.2021.8.26.0100"
    assert "TJSP" in result.court
    assert "32ª VARA CÍVEL" in result.vara
    assert "SÃO PAULO" in result.comarca

    # Parties
    assert "CONDOMÍNIO EDIFÍCIO VILA REAL" in result.exequente
    assert "MARCOS ROBERTO DA SILVA" in result.executado

    # Financials
    assert result.appraisal_value == 1200000.00
    assert result.stage_1_price == 1200000.00
    assert result.stage_1_date is not None
    assert result.stage_1_date.day == 10
    assert result.stage_1_date.month == 12
    assert result.stage_1_date.year == 2026

    assert result.stage_2_price == 600000.00
    assert result.stage_2_discount_pct == 50.0
    assert result.stage_2_date is not None
    assert result.stage_2_date.day == 13
    assert result.stage_2_date.month == 12

    # Registry & specs
    assert result.matricula == "45.892"
    assert "4º OFICIAL DE REGISTRO DE IMÓVEIS" in result.cartorio_rgi
    assert result.iptu_code == "015.082.0144-8"
    assert result.usable_area_m2 == 118.50
    assert result.total_area_m2 == 182.30
    assert result.parking_spots == 2

    # Debts
    assert result.debt_condominio == 85420.15
    assert result.debt_iptu == 32180.00
    assert result.subrogates_debts is True
    assert result.is_occupied is True
