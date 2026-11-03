"""Scraper adapter for Portal Zuk (Zukerman Leilões) properties."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from dateutil import parser as date_parser

from leiloar.models.auction import (
    AuctionLot,
    AuctionSourceType,
    AuctionStage,
    AuctionStatus,
)
from leiloar.scrapers.base import BaseScraper
from leiloar.scrapers.registry import register_scraper

logger = logging.getLogger("leiloar.scrapers.portal_zuk")


@register_scraper("portal_zuk")
class PortalZukScraper(BaseScraper):
    """Scrapes bank and judicial auctions from Portal Zuk."""

    source_name: str = "portal_zuk"
    source_type: str = "extrajudicial_bank"
    default_delay_seconds: float = 2.0

    def parse_card(self, data: Dict[str, Any]) -> AuctionLot:
        """Parse raw Zukerman property JSON/data item."""
        lot_id = f"zuk_{data.get('id', data.get('codigo', 'unknown'))}"
        title = data.get("titulo") or f"Imóvel em {data.get('cidade', 'São Paulo')}/{data.get('uf', 'SP')}"
        appraisal = float(data.get("valor_avaliacao") or data.get("valor_mercado") or 0.0)
        minimum_bid = float(data.get("valor_lance_inicial") or data.get("valor_venda") or appraisal)

        discount_pct = 0.0
        if appraisal > 0 and minimum_bid > 0:
            discount_pct = round(((appraisal - minimum_bid) / appraisal) * 100.0, 2)

        tipo = (data.get("tipo_leilao") or "").lower()
        if "extrajudicial" in tipo:
            source_type = AuctionSourceType.EXTRAJUDICIAL_BANK
        elif "judicial" in tipo:
            source_type = AuctionSourceType.JUDICIAL
        else:
            source_type = AuctionSourceType.EXTRAJUDICIAL_BANK

        return AuctionLot(
            lot_id=lot_id,
            title=title,
            description=data.get("descricao", ""),
            category=data.get("categoria", "imovel_residencial"),
            source_type=source_type,
            status=AuctionStatus.OPEN,
            appraisal_value=appraisal,
            minimum_bid=minimum_bid,
            current_discount_pct=discount_pct,
            stage_1_price=appraisal,
            stage_2_price=minimum_bid if discount_pct > 0 else None,
            occupied=data.get("ocupado", None),
            address=data.get("endereco"),
            neighborhood=data.get("bairro"),
            city=data.get("cidade", "São Paulo"),
            state=data.get("uf", "SP"),
            postal_code=data.get("cep"),
            url=data.get("url") or f"https://www.portalzuk.com.br/imovel/{data.get('id', '')}",
            auctioneer_name="Zukerman Leilões",
            raw_metadata=data,
        )

    async def scrape(self, **kwargs: Any) -> List[AuctionLot]:
        """Scrape active listings from Portal Zuk."""
        # Provides extensible scraping hook; mock fallback if offline
        mock_items = kwargs.get("mock_items")
        if mock_items:
            return [self.parse_card(item) for item in mock_items]
        return []
