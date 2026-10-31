"""Legal public notice (Edital de Leilão Judicial) text parser and extractor."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from dateutil import parser as date_parser

from leiloar.parsers.cnj_validator import extract_cnj_numbers, parse_cnj


def parse_brazilian_currency(val_str: str) -> float:
    """Convert Brazilian currency string (e.g. 'R$ 1.200.000,00' or '600.000,00') to float."""
    if not val_str:
        return 0.0
    clean = re.sub(r"[^\d,\.]", "", val_str).strip(".,")
    # Remove thousand dot separators, replace comma with dot
    if "," in clean and "." in clean:
        clean = clean.replace(".", "").replace(",", ".")
    elif "," in clean:
        clean = clean.replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0


@dataclass
class ParsedEdital:
    """Structured extraction result from a judicial auction edital."""
    raw_text_length: int
    cnj_number: Optional[str] = None
    court: Optional[str] = None
    vara: Optional[str] = None
    comarca: Optional[str] = None
    exequente: Optional[str] = None
    executado: Optional[str] = None
    appraisal_value: float = 0.0
    stage_1_date: Optional[datetime] = None
    stage_1_price: Optional[float] = None
    stage_2_date: Optional[datetime] = None
    stage_2_price: Optional[float] = None
    stage_2_discount_pct: float = 0.0
    matricula: Optional[str] = None
    cartorio_rgi: Optional[str] = None
    iptu_code: Optional[str] = None
    debt_condominio: float = 0.0
    debt_iptu: float = 0.0
    subrogates_debts: bool = True
    is_occupied: bool = True
    usable_area_m2: Optional[float] = None
    total_area_m2: Optional[float] = None
    parking_spots: Optional[int] = None
    extra_metadata: Dict[str, str] = field(default_factory=dict)


class JudicialEditalParser:
    """Extracts critical financial, legal, and asset data from judicial edital texts."""

    RE_EXEQUENTE = re.compile(r"EXEQUENTE\s*:\s*([^\n\r;]+)", re.IGNORECASE)
    RE_EXECUTADO = re.compile(r"EXECUTADO\s*:\s*([^\n\r;]+)", re.IGNORECASE)
    RE_VARA = re.compile(r"(\d+ª\s+VARA\s+[A-ZÀ-Ú\s]+)", re.IGNORECASE)
    RE_COMARCA = re.compile(r"COMARCA\s+DE\s+([A-ZÀ-Ú\s/]+)", re.IGNORECASE)
    
    # Financials
    RE_AVALIACAO = re.compile(
        r"(?:avaliad[oa]|avaliação|valor\s+da\s+avaliação)[^\d\n\r]*R\$\s*([\d\.,]+)",
        re.IGNORECASE
    )
    RE_PRACA_1 = re.compile(
        r"1ª\s*PRA[ÇC]A[^\n\r]*?(\d{1,2}/\d{1,2}/\d{4})[^\n\r]*?(?:R\$\s*([\d\.,]+))?",
        re.IGNORECASE
    )
    RE_PRACA_2 = re.compile(
        r"2ª\s*PRA[ÇC]A[^\n\r]*?(\d{1,2}/\d{1,2}/\d{4})[^\n\r]*?(?:(\d{1,2})%|R\$\s*([\d\.,]+))",
        re.IGNORECASE
    )
    
    # Real estate specifics
    RE_MATRICULA = re.compile(r"matr[íi]cula\s+(?:sob\s+)?n[ºo°]?\s*([\d\.]+)", re.IGNORECASE)
    RE_CARTORIO = re.compile(r"(\d+º\s+OFICIAL\s+DE\s+REGISTRO\s+DE\s+IMÓVEIS[^\n\r,\.]*)", re.IGNORECASE)
    RE_IPTU_INSCRICAO = re.compile(r"(?:SQL|inscrição\s+municipal|contribuinte)[^\d\n\r]*([\d\.\-]+)", re.IGNORECASE)
    RE_AREA_PRIVATIVA = re.compile(r"área\s+privativa[^\d\n\r]*([\d\.,]+)\s*m²", re.IGNORECASE)
    RE_AREA_TOTAL = re.compile(r"área\s+(?:total|construída)[^\d\n\r]*([\d\.,]+)\s*m²", re.IGNORECASE)
    RE_VAGAS = re.compile(r"(\d+)\s*(?:\([^\)]+\)\s*)?vagas?", re.IGNORECASE)

    # Debts
    RE_DEBITO_COND = re.compile(r"(?:débito\s+de\s+condomínio|cotas?\s+condominia(?:is|l))[^\d\n\r]*R\$\s*([\d\.,]+)", re.IGNORECASE)
    RE_DEBITO_IPTU = re.compile(r"(?:débitos?\s+fiscais|débitos?\s+de\s+IPTU)[^\d\n\r]*R\$\s*([\d\.,]+)", re.IGNORECASE)

    def parse(self, text: str) -> ParsedEdital:
        """Parse raw text of a Brazilian judicial auction announcement."""
        res = ParsedEdital(raw_text_length=len(text))

        # 1. CNJ & Court
        cnj_list = extract_cnj_numbers(text)
        if cnj_list:
            res.cnj_number = cnj_list[0]
            parsed_cnj = parse_cnj(res.cnj_number)
            if parsed_cnj:
                res.court = parsed_cnj.court_name

        m_vara = self.RE_VARA.search(text)
        if m_vara:
            res.vara = m_vara.group(1).strip()

        m_comarca = self.RE_COMARCA.search(text)
        if m_comarca:
            res.comarca = m_comarca.group(1).split("-")[0].strip()

        # 2. Parties
        m_exeq = self.RE_EXEQUENTE.search(text)
        if m_exeq:
            res.exequente = m_exeq.group(1).strip()

        m_exec = self.RE_EXECUTADO.search(text)
        if m_exec:
            res.executado = m_exec.group(1).strip()

        # 3. Appraisal & Praças
        m_aval = self.RE_AVALIACAO.search(text)
        if m_aval:
            res.appraisal_value = parse_brazilian_currency(m_aval.group(1))

        # 1ª Praça Section
        m_sec_p1 = re.search(r"1ª\s*PRA[ÇC]A:(.*?)(?:2ª\s*PRA[ÇC]A|DÉBITOS|\Z)", text, re.DOTALL | re.IGNORECASE)
        sec_p1_text = m_sec_p1.group(1) if m_sec_p1 else text
        m_date_p1 = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", sec_p1_text)
        if m_date_p1:
            try:
                res.stage_1_date = datetime.strptime(m_date_p1.group(1), "%d/%m/%Y")
            except Exception:
                pass
        m_price_p1 = re.search(r"R\$\s*([\d\.,]+)", sec_p1_text)
        if m_price_p1:
            res.stage_1_price = parse_brazilian_currency(m_price_p1.group(1))
        else:
            res.stage_1_price = res.appraisal_value

        # 2ª Praça Section
        m_sec_p2 = re.search(r"2ª\s*PRA[ÇC]A:(.*?)(?:DÉBITOS|SITUAÇÃO|COMISSÃO|\Z)", text, re.DOTALL | re.IGNORECASE)
        if m_sec_p2:
            sec_p2_text = m_sec_p2.group(1)
            # Find date
            m_date_p2 = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", sec_p2_text)
            if m_date_p2:
                try:
                    res.stage_2_date = datetime.strptime(m_date_p2.group(1), "%d/%m/%Y")
                except Exception:
                    pass

            # Find percentage or price
            m_pct = re.search(r"(\d{1,2})%\s*(?:\([^\)]+\)\s*)?(?:do\s+valor)?", sec_p2_text)
            m_price_p2 = re.search(r"R\$\s*([\d\.,]+)", sec_p2_text)

            if m_price_p2:
                res.stage_2_price = parse_brazilian_currency(m_price_p2.group(1))
                if res.appraisal_value > 0:
                    res.stage_2_discount_pct = round(
                        ((res.appraisal_value - res.stage_2_price) / res.appraisal_value) * 100.0, 2
                    )
            elif m_pct and res.appraisal_value > 0:
                pct = float(m_pct.group(1))
                res.stage_2_discount_pct = 100.0 - pct
                res.stage_2_price = round(res.appraisal_value * (pct / 100.0), 2)

        # 4. Property Registry & Physical specs
        m_mat = self.RE_MATRICULA.search(text)
        if m_mat:
            res.matricula = m_mat.group(1).strip()

        m_cart = self.RE_CARTORIO.search(text)
        if m_cart:
            res.cartorio_rgi = m_cart.group(1).strip()

        m_iptu_insc = self.RE_IPTU_INSCRICAO.search(text)
        if m_iptu_insc:
            res.iptu_code = m_iptu_insc.group(1).strip().rstrip(".")

        m_priv = self.RE_AREA_PRIVATIVA.search(text)
        if m_priv:
            res.usable_area_m2 = parse_brazilian_currency(m_priv.group(1))

        m_tot = self.RE_AREA_TOTAL.search(text)
        if m_tot:
            res.total_area_m2 = parse_brazilian_currency(m_tot.group(1))

        m_vagas = self.RE_VAGAS.search(text)
        if m_vagas:
            res.parking_spots = int(m_vagas.group(1))

        # 5. Debts and Subrogation
        m_dcond = self.RE_DEBITO_COND.search(text)
        if m_dcond:
            res.debt_condominio = parse_brazilian_currency(m_dcond.group(1))

        m_diptu = self.RE_DEBITO_IPTU.search(text)
        if m_diptu:
            res.debt_iptu = parse_brazilian_currency(m_diptu.group(1))

        # Check subrogation rule (Art. 130 parágrafo único CTN)
        text_lower = text.lower()
        if "sub-rogam" in text_lower or "sub-rogação" in text_lower or "art. 130" in text_lower:
            res.subrogates_debts = True
        elif "por conta do arrematante" in text_lower and "tributos" in text_lower:
            res.subrogates_debts = False

        # 6. Occupancy
        if "desocupado" in text_lower:
            res.is_occupied = False
        else:
            res.is_occupied = True

        return res
