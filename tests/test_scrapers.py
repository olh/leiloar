"""Tests for auction scrapers and registry."""

from pathlib import Path
import pytest
from leiloar.models.auction import AuctionSourceType
from leiloar.scrapers import get_scraper_class, list_registered_scrapers
from leiloar.scrapers.caixa import CaixaAuctionScraper


def test_scraper_registry():
    registered = list_registered_scrapers()
    assert "caixa" in registered
    cls = get_scraper_class("caixa")
    assert cls is CaixaAuctionScraper


@pytest.mark.anyio
async def test_caixa_scraper_parsing_fixture():
    scraper = CaixaAuctionScraper()
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "sample_caixa_data.json"
    assert fixture_path.exists(), "Sample Caixa fixture file must exist"

    lots = await scraper.scrape_from_fixture(fixture_path)
    assert len(lots) == 3

    lot1 = lots[0]
    assert lot1.lot_id == "caixa_8444401234567"
    assert lot1.state == "SP"
    assert lot1.city == "São Paulo"
    assert lot1.neighborhood == "Mooca"
    assert lot1.source_type == AuctionSourceType.EXTRAJUDICIAL_BANK
    assert lot1.appraisal_value == 480000.00
    assert lot1.minimum_bid == 264000.00
    assert lot1.current_discount_pct == 45.0
    assert lot1.occupied is True
    assert lot1.raw_metadata["permite_financiamento"] is True

    lot2 = lots[1]
    assert lot2.city == "Campinas"
    assert lot2.occupied is False
    assert lot2.current_discount_pct == 50.0

    await scraper.close()
