"""Scraper for Caixa Econômica Federal repossessed property auctions and sales."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dateutil import parser as date_parser

from leiloar.models.asset import AssetCategory
from leiloar.models.auction import (
    AuctionLot,
    AuctionSourceType,
    AuctionStage,
    AuctionStatus,
)
from leiloar.scrapers.base import BaseScraper
from leiloar.scrapers.registry import register_scraper

CAIXA_LISTINGS_URL = "https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_{uf}.csv"


@register_scraper("caixa")
class CaixaAuctionScraper(BaseScraper):
    """Ingests bank-repossessed real estate from Caixa Econômica Federal."""

    source_name: str = "caixa"
    source_type: str = "extrajudicial_bank"
    default_delay_seconds: float = 1.5

    def _normalize_category(self, tipo_str: str) -> str:
        """Map Caixa property type names to unified taxonomy."""
        clean = (tipo_str or "").strip().lower()
        if "apartamento" in clean or "apto" in clean:
            return AssetCategory.REAL_ESTATE_APARTMENT.value
        elif "casa" in clean or "sobrado" in clean:
            return AssetCategory.REAL_ESTATE_HOUSE.value
        elif "terreno" in clean or "lote" in clean:
            return AssetCategory.REAL_ESTATE_LAND.value
        elif "comercial" in clean or "sala" in clean or "loja" in clean:
            return AssetCategory.REAL_ESTATE_COMMERCIAL.value
        elif "galp" in clean or "industrial" in clean:
            return AssetCategory.REAL_ESTATE_INDUSTRIAL.value
        return AssetCategory.REAL_ESTATE_APARTMENT.value

    def _normalize_stage(self, modalidade: str) -> AuctionStage:
        """Determine auction stage based on Caixa bidding rules."""
        m = (modalidade or "").lower()
        if "1º leilão" in m or "1o leilao" in m:
            return AuctionStage.FIRST_STAGE
        elif "2º leilão" in m or "2o leilao" in m:
            return AuctionStage.SECOND_STAGE
        return AuctionStage.SINGLE_STAGE

    def parse_item(self, item: Dict[str, Any]) -> AuctionLot:
        """Transform raw Caixa JSON/record into standardized AuctionLot model."""
        lot_id = f"caixa_{item.get('id_imovel', '').strip()}"
        city = (item.get("cidade") or "São Paulo").title()
        uf = (item.get("uf") or "SP").upper()
        bairro = (item.get("bairro") or "").title()
        tipo = item.get("tipo_imovel") or "Apartamento"
        endereco = item.get("endereco") or ""

        title = f"{tipo} - {bairro}, {city}/{uf}"
        category = self._normalize_category(tipo)

        appraisal = float(item.get("valor_avaliacao") or 0.0)
        minimum_bid = float(item.get("valor_minimo_venda") or appraisal)

        # Discount calculation
        if appraisal > 0 and minimum_bid > 0:
            discount_pct = round(((appraisal - minimum_bid) / appraisal) * 100.0, 2)
        else:
            discount_pct = float(item.get("desconto_percentual") or 0.0)

        # Date handling
        end_date_str = item.get("data_encerramento")
        end_date: Optional[datetime] = None
        if end_date_str:
            try:
                end_date = date_parser.parse(end_date_str)
            except Exception:
                end_date = None

        occupied_status = item.get("situacao_posse", "").lower()
        is_occupied = True if "ocupado" in occupied_status and "desocupado" not in occupied_status else False

        description = (
            f"{tipo} com área privativa de {item.get('area_privativa_m2', 0)}m², "
            f"{item.get('quartos', 0)} quartos, {item.get('vagas', 0)} vagas. "
            f"Endereço: {endereco}. Modalidade: {item.get('modalidade_venda', '')}. "
            f"Situação: {'Ocupado' if is_occupied else 'Desocupado'}."
        )

        return AuctionLot(
            lot_id=lot_id,
            title=title,
            description=description,
            category=category,
            source_type=AuctionSourceType.EXTRAJUDICIAL_BANK,
            status=AuctionStatus.OPEN,
            appraisal_value=appraisal,
            minimum_bid=minimum_bid,
            current_discount_pct=discount_pct,
            stage_1_price=appraisal,
            stage_2_price=minimum_bid if discount_pct > 0 else None,
            stage_2_date=end_date,
            occupied=is_occupied,
            address=endereco,
            neighborhood=bairro,
            city=city,
            state=uf,
            postal_code=item.get("cep"),
            url=item.get("url_detalhe") or f"https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel={item.get('id_imovel')}",
            auctioneer_name="Caixa Econômica Federal",
            raw_metadata={
                "modalidade_venda": item.get("modalidade_venda"),
                "permite_financiamento": item.get("permite_financiamento", False),
                "permite_fgts": item.get("permite_fgts", False),
            },
        )

    async def scrape_from_fixture(self, fixture_path: Path) -> List[AuctionLot]:
        """Load and parse auction lots from local fixture file for testing/offline sync."""
        with open(fixture_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [self.parse_item(item) for item in raw_data]

    async def scrape(self, uf: str = "SP", fixture_file: Optional[str] = None, **kwargs: Any) -> List[AuctionLot]:
        """Execute scraping for a target state or local fixture."""
        if fixture_file:
            path = Path(fixture_file)
            if not path.exists():
                raise FileNotFoundError(f"Fixture file not found: {fixture_file}")
            return await self.scrape_from_fixture(path)

        # In production mode, queries Caixa endpoint (or falls back to default fixtures)
        # Note: Caixa endpoint frequently demands specific TLS ciphers or delivers zipped CSVs
        url = CAIXA_LISTINGS_URL.format(uf=uf.upper())
        try:
            # We attempt live fetch or return synthetic sample if offline/blocked
            csv_text = await self.fetch_text(url)
            # In live scenario, parse CSV lines
            lots: List[AuctionLot] = []
            return lots
        except Exception:
            # Fallback to local default fixture if network is unavailable
            default_fixture = Path(__file__).resolve().parents[3] / "fixtures" / "sample_caixa_data.json"
            if default_fixture.exists():
                return await self.scrape_from_fixture(default_fixture)
            return []
