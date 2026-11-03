"""Scraper adapter for Mega Leilões judicial and extrajudicial lots."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from leiloar.models.auction import (
    AuctionLot,
    AuctionSourceType,
    AuctionStatus,
    LegalProcess,
)
from leiloar.parsers.cnj_validator import extract_cnj_numbers
from leiloar.scrapers.base import BaseScraper
from leiloar.scrapers.registry import register_scraper

logger = logging.getLogger("leiloar.scrapers.mega_leiloes")


@register_scraper("mega_leiloes")
class MegaLeiloesScraper(BaseScraper):
    """Scrapes judicial lawsuits and lots from Mega Leilões."""

    source_name: str = "mega_leiloes"
    source_type: str = "judicial"
    default_delay_seconds: float = 2.0

    def parse_lot(self, data: Dict[str, Any]) -> AuctionLot:
        """Transform Mega Leilões item dictionary to AuctionLot."""
        lot_id = f"mega_{data.get('id', data.get('lote_numero', '0'))}"
        title = data.get("nome") or data.get("titulo") or "Lote em Leilão Judicial"
        desc = data.get("descricao") or ""

        appraisal = float(data.get("valor_avaliacao") or 0.0)
        minimum_bid = float(data.get("valor_lance_minimo") or data.get("valor_2a_praca") or appraisal)

        discount_pct = 0.0
        if appraisal > 0 and minimum_bid > 0:
            discount_pct = round(((appraisal - minimum_bid) / appraisal) * 100.0, 2)

        # Detect CNJ lawsuit if present in description or dedicated field
        legal_proc = None
        cnj_str = data.get("numero_processo")
        if not cnj_str:
            found = extract_cnj_numbers(desc)
            if found:
                cnj_str = found[0]

        if cnj_str:
            legal_proc = LegalProcess(
                cnj_number=cnj_str,
                court=data.get("tribunal", "TJSP"),
                vara=data.get("vara", ""),
                comarca=data.get("comarca", data.get("cidade", "São Paulo")),
            )

        return AuctionLot(
            lot_id=lot_id,
            title=title,
            description=desc,
            category=data.get("categoria", "imovel_residencial"),
            source_type=AuctionSourceType.JUDICIAL,
            status=AuctionStatus.OPEN,
            appraisal_value=appraisal,
            minimum_bid=minimum_bid,
            current_discount_pct=discount_pct,
            stage_1_price=appraisal,
            stage_2_price=minimum_bid if discount_pct > 0 else None,
            legal_process=legal_proc,
            address=data.get("endereco"),
            neighborhood=data.get("bairro"),
            city=data.get("cidade", "São Paulo"),
            state=data.get("uf", "SP"),
            postal_code=data.get("cep"),
            url=data.get("url") or f"https://www.megaleiloes.com.br/imoveis/{data.get('id', '')}",
            auctioneer_name="Mega Leilões",
            raw_metadata=data,
        )

    async def scrape(self, **kwargs: Any) -> List[AuctionLot]:
        """Scrape active listings from Mega Leilões."""
        mock_items = kwargs.get("mock_items")
        if mock_items:
            return [self.parse_lot(item) for item in mock_items]
        return []
