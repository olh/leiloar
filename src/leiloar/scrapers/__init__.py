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

__all__ = [
    "BaseScraper",
    "ScraperException",
    "ScraperRateLimitError",
    "register_scraper",
    "get_scraper_class",
    "list_registered_scrapers",
]
