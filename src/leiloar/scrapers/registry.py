"""Registry for discovering and instantiating auction scrapers."""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Type
from leiloar.scrapers.base import BaseScraper

logger = logging.getLogger("leiloar.scrapers.registry")

_SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {}


def register_scraper(name: str) -> Callable[[Type[BaseScraper]], Type[BaseScraper]]:
    """Class decorator to register a scraper implementation."""
    def decorator(cls: Type[BaseScraper]) -> Type[BaseScraper]:
        cls.source_name = name
        _SCRAPER_REGISTRY[name.lower()] = cls
        logger.debug(f"Registered auction scraper: {name}")
        return cls
    return decorator


def get_scraper_class(name: str) -> Type[BaseScraper]:
    """Retrieve scraper class by registered identifier."""
    name_clean = name.lower()
    if name_clean not in _SCRAPER_REGISTRY:
        available = ", ".join(_SCRAPER_REGISTRY.keys())
        raise KeyError(f"Scraper '{name}' not found. Available: {available}")
    return _SCRAPER_REGISTRY[name_clean]


def list_registered_scrapers() -> List[str]:
    """Return all currently registered scraper identifiers."""
    return sorted(list(_SCRAPER_REGISTRY.keys()))
