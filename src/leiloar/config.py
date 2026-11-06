"""Configuration settings loaded from environment or local .env file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime application and pipeline configuration."""
    database_path: str = Field(
        default=os.getenv("LEILOAR_DATABASE_PATH", "leiloar_radar.db"),
        description="SQLite database path or postgresql:// connection URL",
    )
    api_host: str = Field(
        default=os.getenv("LEILOAR_API_HOST", "0.0.0.0"),
        description="FastAPI bind host address",
    )
    api_port: int = Field(
        default=int(os.getenv("LEILOAR_API_PORT", "8000")),
        description="FastAPI HTTP port",
    )
    default_uf: str = Field(
        default=os.getenv("LEILOAR_DEFAULT_UF", "SP"),
        description="Default Brazilian state (UF) for scraper runs",
    )
    request_delay_seconds: float = Field(
        default=float(os.getenv("LEILOAR_REQUEST_DELAY_SECONDS", "1.5")),
        description="Polite rate limiting delay between crawler requests",
    )
    log_level: str = Field(
        default=os.getenv("LEILOAR_LOG_LEVEL", "INFO"),
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )


settings = Settings()
