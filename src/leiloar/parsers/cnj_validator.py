"""Brazilian CNJ (Conselho Nacional de Justiça) legal process validator and parser.

Follows CNJ Resolution nº 65/2008 standardizing judicial lawsuit identifiers:
Format: NNNNNNN-DD.YYYY.J.TR.OOOO (20 numerical digits)
Algorithm: ISO 7064 Modulo 97-10 check digit verification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

# Segment names indexed by digit J
JUDICIARY_SEGMENTS: Dict[int, str] = {
    1: "Supremo Tribunal Federal (STF)",
    2: "Conselho Nacional de Justiça (CNJ)",
    3: "Superior Tribunal de Justiça (STJ)",
    4: "Justiça Federal (TRF)",
    5: "Justiça do Trabalho (TRT)",
    6: "Justiça Eleitoral (TRE)",
    7: "Justiça Militar da União",
    8: "Justiça dos Estados e DF (TJ)",
    9: "Justiça Militar Estadual",
}

# State Court (TJ) codes (J=8)
STATE_COURTS: Dict[int, str] = {
    1: "TJAC", 2: "TJAL", 3: "TJAP", 4: "TJAM", 5: "TJBA", 6: "TJCE",
    7: "TJDF", 8: "TJES", 9: "TJGO", 10: "TJMA", 11: "TJMT", 12: "TJMS",
    13: "TJMG", 14: "TJPA", 15: "TJPB", 16: "TJPR", 17: "TJPE", 18: "TJPI",
    19: "TJRJ", 20: "TJRN", 21: "TJRS", 22: "TJRO", 23: "TJRR", 24: "TJSC",
    25: "TJSE", 26: "TJSP", 27: "TJTO",
}

# Federal Regional Courts (TRF) (J=4)
FEDERAL_COURTS: Dict[int, str] = {
    1: "TRF1 (DF, GO, TO, MT, BA, etc.)",
    2: "TRF2 (RJ, ES)",
    3: "TRF3 (SP, MS)",
    4: "TRF4 (RS, PR, SC)",
    5: "TRF5 (PE, CE, AL, PB, RN, SE)",
    6: "TRF6 (MG)",
}

# Regional Labor Courts (TRT) (J=5)
LABOR_COURTS: Dict[int, str] = {
    1: "TRT1 (RJ)", 2: "TRT2 (SP - Capital/Grande SP)", 3: "TRT3 (MG)",
    4: "TRT4 (RS)", 5: "TRT5 (BA)", 6: "TRT6 (PE)", 7: "TRT7 (CE)",
    8: "TRT8 (PA/AP)", 9: "TRT9 (PR)", 10: "TRT10 (DF/TO)", 11: "TRT11 (AM/RR)",
    12: "TRT12 (SC)", 13: "TRT13 (PB)", 14: "TRT14 (RO/AC)", 15: "TRT15 (SP - Interior/Campinas)",
    16: "TRT16 (MA)", 17: "TRT17 (ES)", 18: "TRT18 (GO)", 19: "TRT19 (AL)",
    20: "TRT20 (SE)", 21: "TRT21 (RN)", 22: "TRT22 (PI)", 23: "TRT23 (MT)",
    24: "TRT24 (MS)",
}

# Regex matching standard formatted CNJ or unformatted 20-digit string
CNJ_FORMATTED_REGEX = re.compile(r"\b(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})\b")
CNJ_UNFORMATTED_REGEX = re.compile(r"\b(\d{20})\b")


@dataclass
class CNJMetadata:
    """Parsed and validated components of a CNJ judicial process identifier."""
    formatted: str
    raw_digits: str
    order_number: int
    check_digits: str
    year: int
    segment_code: int
    segment_name: str
    court_code: int
    court_name: str
    origin_unit: int
    is_valid: bool


def compute_cnj_check_digits(
    order_number: int,
    year: int,
    segment_code: int,
    court_code: int,
    origin_unit: int,
) -> str:
    """Calculate the 2-digit ISO 7064 Modulo 97-10 check digits for a lawsuit."""
    order_str = f"{order_number:07d}"
    year_str = f"{year:04d}"
    j_str = str(segment_code)
    tr_str = f"{court_code:02d}"
    orig_str = f"{origin_unit:04d}"

    # Concatenate: NNNNNNN + YYYY + J + TR + OOOO + '00'
    base_number_str = f"{order_str}{year_str}{j_str}{tr_str}{orig_str}00"
    remainder = int(base_number_str) % 97
    check_val = 98 - remainder
    return f"{check_val:02d}"


def validate_cnj(cnj_str: str) -> bool:
    """Validate whether a CNJ lawsuit string has valid structure and Modulo 97 check digits."""
    digits_only = re.sub(r"\D", "", cnj_str)
    if len(digits_only) != 20:
        return False

    order_str = digits_only[0:7]
    check_digits = digits_only[7:9]
    year_str = digits_only[9:13]
    j_str = digits_only[13:14]
    tr_str = digits_only[14:16]
    orig_str = digits_only[16:20]

    # ISO 7064 check: concatenate NNNNNNN + YYYY + J + TR + OOOO + DD
    # When correct, int(...) % 97 MUST equal 1
    eval_str = f"{order_str}{year_str}{j_str}{tr_str}{orig_str}{check_digits}"
    return int(eval_str) % 97 == 1


def resolve_court_name(segment_code: int, court_code: int) -> str:
    """Resolve human-readable court acronym from segment and tribunal codes."""
    if segment_code == 8:
        return STATE_COURTS.get(court_code, f"TJ-{court_code:02d}")
    elif segment_code == 4:
        return FEDERAL_COURTS.get(court_code, f"TRF-{court_code:02d}")
    elif segment_code == 5:
        return LABOR_COURTS.get(court_code, f"TRT-{court_code:02d}")
    elif segment_code == 1:
        return "STF"
    elif segment_code == 2:
        return "CNJ"
    elif segment_code == 3:
        return "STJ"
    return f"Tribunal-{segment_code}-{court_code:02d}"


def parse_cnj(cnj_str: str) -> Optional[CNJMetadata]:
    """Parse and decompose a CNJ lawsuit number into its jurisdictional metadata."""
    digits = re.sub(r"\D", "", cnj_str)
    if len(digits) != 20:
        return None

    order_num = int(digits[0:7])
    check_digits = digits[7:9]
    year = int(digits[9:13])
    segment_code = int(digits[13:14])
    court_code = int(digits[14:16])
    origin_unit = int(digits[16:20])

    is_valid = validate_cnj(digits)
    formatted = f"{order_num:07d}-{check_digits}.{year:04d}.{segment_code}.{court_code:02d}.{origin_unit:04d}"
    segment_name = JUDICIARY_SEGMENTS.get(segment_code, "Outro")
    court_name = resolve_court_name(segment_code, court_code)

    return CNJMetadata(
        formatted=formatted,
        raw_digits=digits,
        order_number=order_num,
        check_digits=check_digits,
        year=year,
        segment_code=segment_code,
        segment_name=segment_name,
        court_code=court_code,
        court_name=court_name,
        origin_unit=origin_unit,
        is_valid=is_valid,
    )


def extract_cnj_numbers(text: str) -> List[str]:
    """Extract and validate all CNJ formatted or unformatted numbers found inside a raw text."""
    found: List[str] = []
    
    # Check formatted occurrences
    for match in CNJ_FORMATTED_REGEX.finditer(text):
        full_match = match.group(0)
        if validate_cnj(full_match) and full_match not in found:
            found.append(full_match)

    # Check unformatted occurrences
    for match in CNJ_UNFORMATTED_REGEX.finditer(text):
        digits = match.group(1)
        if validate_cnj(digits):
            parsed = parse_cnj(digits)
            if parsed and parsed.formatted not in found:
                found.append(parsed.formatted)

    return found
