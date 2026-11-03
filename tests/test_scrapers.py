"""Tests for auction scrapers and registry."""

from pathlib import Path
import pytest
from leiloar.models.auction import AuctionSourceType
from leiloar.scrapers import get_scraper_class, list_registered_scrapers
from leiloar.scrapers.caixa import CaixaAuctionScraper
from leiloar.scrapers.portal_zuk import PortalZukScraper
from leiloar.scrapers.mega_leiloes import MegaLeiloesScraper


def test_scraper_registry():
    registered = list_registered_scrapers()
    assert "caixa" in registered
    assert "portal_zuk" in registered
    assert "mega_leiloes" in registered

    cls_caixa = get_scraper_class("caixa")
    assert cls_caixa is CaixaAuctionScraper

    cls_zuk = get_scraper_class("portal_zuk")
    assert cls_zuk is PortalZukScraper

    cls_mega = get_scraper_class("mega_leiloes")
    assert cls_mega is MegaLeiloesScraper


@pytest.mark.anyio
async def test_portal_zuk_parsing():
    scraper = PortalZukScraper()
    item = {
        "id": "10492",
        "titulo": "Apartamento Vila Mariana",
        "cidade": "São Paulo",
        "uf": "SP",
        "valor_avaliacao": 800000.0,
        "valor_lance_inicial": 400000.0,
        "tipo_leilao": "Extrajudicial",
    }
    lot = scraper.parse_card(item)
    assert lot.lot_id == "zuk_10492"
    assert lot.current_discount_pct == 50.0
    assert lot.source_type == AuctionSourceType.EXTRAJUDICIAL_BANK


@pytest.mark.anyio
async def test_mega_leiloes_parsing():
    scraper = MegaLeiloesScraper()
    item = {
        "id": "ML9901",
        "titulo": "Casa em Condomínio Fechado",
        "cidade": "Barueri",
        "uf": "SP",
        "valor_avaliacao": 1500000.0,
        "valor_lance_minimo": 750000.0,
        "numero_processo": "1002345-67.2021.8.26.0100",
    }
    lot = scraper.parse_lot(item)
    assert lot.lot_id == "mega_ML9901"
    assert lot.current_discount_pct == 50.0
    assert lot.source_type == AuctionSourceType.JUDICIAL
    assert lot.legal_process is not None
    assert lot.legal_process.cnj_number == "1002345-67.2021.8.26.0100"


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
