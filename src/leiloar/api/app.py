"""FastAPI application factory for Leiloar Radar service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from leiloar.api.routes import analytics_router, auctions_router
from leiloar.storage.database import DatabaseManager
from leiloar.storage.repository import AuctionRepository

logger = logging.getLogger("leiloar.api")


def create_app(db_path: Optional[str] = None) -> FastAPI:
    """Create and configure FastAPI application instance."""
    db_manager = DatabaseManager(db_path)
    repository = AuctionRepository(db_manager)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Initializing Leiloar Radar API services...")
        app.state.db = db_manager
        app.state.repository = repository
        yield
        logger.info("Shutting down Leiloar Radar API...")
        db_manager.close()

    app = FastAPI(
        title="Leiloar Radar API",
        description="SaaS auction research and classification framework powering https://leiloar.com/radar-leiloes",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Set up app state for dependencies
    app.state.db = db_manager
    app.state.repository = repository

    # CORS configuration for Leiloar web application
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://leiloar.com", "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "leiloar-radar-api",
            "version": "0.1.0",
        }

    # Mount API routers
    app.include_router(auctions_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")

    return app
