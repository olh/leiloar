"""Market analytics and aggregate statistics endpoints."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, Request
from leiloar.api.routes.auctions import get_repository

router = APIRouter(prefix="/radar", tags=["Analytics"])


@router.get("/stats")
async def get_market_statistics(repo=Depends(get_repository)) -> Dict[str, Any]:
    """Return platform overview statistics, average discounts, and geographical breakdown."""
    return repo.get_market_statistics()
