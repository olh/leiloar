"""Tests for Brazilian CNJ legal process parser and Modulo 97 validator."""

import pytest
from leiloar.parsers.cnj_validator import (
    compute_cnj_check_digits,
    extract_cnj_numbers,
    parse_cnj,
    validate_cnj,
)


def test_compute_cnj_check_digits():
    # Example lawsuit: Order 1002345, Year 2021, Segment 8 (TJ), Court 26 (TJSP), Unit 0100
    expected_check = compute_cnj_check_digits(
        order_number=1002345,
        year=2021,
        segment_code=8,
        court_code=26,
        origin_unit=100,
    )
    assert len(expected_check) == 2
    full_cnj = f"1002345-{expected_check}.2021.8.26.0100"
    assert validate_cnj(full_cnj) is True


def test_validate_cnj_valid_and_invalid():
    # Valid generated CNJ
    valid_check = compute_cnj_check_digits(5001234, 2023, 8, 19, 1)  # TJRJ
    valid_cnj = f"5001234-{valid_check}.2023.8.19.0001"
    assert validate_cnj(valid_cnj) is True

    # Corrupted check digits
    invalid_cnj = "5001234-99.2023.8.19.0001"
    assert validate_cnj(invalid_cnj) is False

    # Invalid lengths
    assert validate_cnj("12345") is False
    assert validate_cnj("") is False


def test_parse_cnj_components():
    check = compute_cnj_check_digits(1234567, 2024, 5, 2, 90)  # TRT2
    cnj_str = f"1234567-{check}.2024.5.02.0090"
    parsed = parse_cnj(cnj_str)

    assert parsed is not None
    assert parsed.order_number == 1234567
    assert parsed.year == 2024
    assert parsed.segment_code == 5
    assert "Trabalho" in parsed.segment_name
    assert "TRT2" in parsed.court_name
    assert parsed.court_code == 2
    assert parsed.origin_unit == 90
    assert parsed.is_valid is True


def test_extract_cnj_from_edital_text():
    sample_text = """
    EDITAL DE LEILÃO JUDICIAL E INTIMAÇÃO
    O Doutor Juiz de Direito da 2ª Vara Cível do Foro Central da Comarca de São Paulo,
    na Ação de Execução de Título Extrajudicial promovida pelo Condomínio Edifício Solar,
    Processo nº 1002345-67.2021.8.26.0100 (outro texto qualquer), FAZ SABER...
    Também no processo apenso 0001234-56.2022.8.26.0100 correrão os autos.
    """
    # Replace with mathematically valid numbers
    c1 = compute_cnj_check_digits(1002345, 2021, 8, 26, 100)
    c2 = compute_cnj_check_digits(1234, 2022, 8, 26, 100)
    sample_text = sample_text.replace("1002345-67", f"1002345-{c1}").replace("0001234-56", f"0001234-{c2}")

    extracted = extract_cnj_numbers(sample_text)
    assert len(extracted) == 2
    assert f"1002345-{c1}.2021.8.26.0100" in extracted
