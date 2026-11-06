"""Auction scrapers module."""

from leiloar.scrapers.base import (
    BaseScraper,
    ScraperException,
    ScraperRateLimitError,
)
from leiloar.scrapers.registry import (
    get_scraper_class,
    list_registered_scrapers,
    register_scraper,
)

# Auto-import scraper modules to register them
import leiloar.scrapers.caixa.scraper  # noqa: F401
import leiloar.scrapers.portal_zuk.scraper  # noqa: F401
import leiloar.scrapers.mega_leiloes.scraper  # noqa: F401

__all__ = [
    "BaseScraper",
    "ScraperException",
    "ScraperRateLimitError",
    "register_scraper",
    "get_scraper_class",
    "list_registered_scrapers",
]
