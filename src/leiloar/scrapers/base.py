"""Base asynchronous scraper framework with rate limiting, retries, and headers rotation."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
import aiohttp
from leiloar.models.auction import AuctionLot

logger = logging.getLogger("leiloar.scrapers")

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
]


class ScraperException(Exception):
    """Base exception for scraping operations."""


class ScraperRateLimitError(ScraperException):
    """Raised when an external auction portal responds with HTTP 429 Too Many Requests."""


class BaseScraper(ABC):
    """Abstract base class for all auctioneer and bank data ingestion scrapers."""

    source_name: str = "base"
    source_type: str = "general"
    default_delay_seconds: float = 1.0
    max_retries: int = 3

    def __init__(
        self,
        delay_seconds: Optional[float] = None,
        timeout_seconds: float = 30.0,
        proxy_url: Optional[str] = None,
    ) -> None:
        self.delay_seconds = delay_seconds if delay_seconds is not None else self.default_delay_seconds
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.proxy_url = proxy_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time: float = 0.0

    async def get_session(self) -> aiohttp.ClientSession:
        """Lazily initialize or return existing ClientSession."""
        if self._session is None or self._session.closed:
            headers = {
                "User-Agent": random.choice(DEFAULT_USER_AGENTS),
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
            }
            self._session = aiohttp.ClientSession(headers=headers, timeout=self.timeout)
        return self._session

    async def close(self) -> None:
        """Cleanly close underlying HTTP connection pool."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _throttle(self) -> None:
        """Enforce rate-limiting interval between consecutive requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.delay_seconds:
            sleep_time = self.delay_seconds - elapsed + random.uniform(0.05, 0.2)
            await asyncio.sleep(sleep_time)
        self._last_request_time = time.time()

    async def fetch_text(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Fetch textual/HTML payload with automatic exponential backoff retry."""
        session = await self.get_session()
        for attempt in range(1, self.max_retries + 1):
            await self._throttle()
            try:
                async with session.get(url, params=params, proxy=self.proxy_url) as response:
                    if response.status == 429:
                        wait = (2 ** attempt) + random.uniform(1.0, 3.0)
                        logger.warning(f"Rate limited (429) at {url}. Backing off for {wait:.2f}s...")
                        await asyncio.sleep(wait)
                        continue
                    response.raise_for_status()
                    return await response.text(encoding="utf-8", errors="replace")
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                if attempt == self.max_retries:
                    raise ScraperException(f"Failed to fetch {url} after {self.max_retries} attempts: {err}")
                await asyncio.sleep(1.5 * attempt)
        raise ScraperException(f"Failed to fetch {url}")

    async def fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Fetch and parse JSON endpoint."""
        session = await self.get_session()
        for attempt in range(1, self.max_retries + 1):
            await self._throttle()
            try:
                async with session.get(url, params=params, proxy=self.proxy_url) as response:
                    if response.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    response.raise_for_status()
                    return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                if attempt == self.max_retries:
                    raise ScraperException(f"Failed to fetch JSON {url}: {err}")
                await asyncio.sleep(1.5 * attempt)
        raise ScraperException(f"Failed to fetch JSON {url}")

    @abstractmethod
    async def scrape(self, **kwargs: Any) -> List[AuctionLot]:
        """Execute extraction and return standardized AuctionLot objects."""
        raise NotImplementedError
