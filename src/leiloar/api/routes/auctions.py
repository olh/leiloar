"""Radar search, filtering, and lot details API routes."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request

router = APIRouter(prefix="/radar", tags=["Radar de Leilões"])


def get_repository(request: Request):
    """Retrieve shared AuctionRepository from application state."""
    return request.app.state.repository


@router.get("/lots")
async def list_radar_lots(
    q: Optional[str] = Query(None, description="Free text search (title, city, description)"),
    state: Optional[str] = Query(None, max_length=2, description="Federation state code (UF) e.g. SP, RJ"),
    city: Optional[str] = Query(None, description="City name filter"),
    category: Optional[str] = Query(None, description="Asset category"),
    min_discount: Optional[float] = Query(None, ge=0, le=100, description="Minimum discount percentage"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price in BRL"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum DealScore"),
    source_type: Optional[str] = Query(None, description="judicial or extrajudicial_bank"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    repo=Depends(get_repository),
) -> Dict[str, Any]:
    """Faceted search endpoint powering the interactive Radar de Leilões catalog."""
    offset = (page - 1) * limit
    items, total_count = repo.search_radar(
        query=q,
        state=state,
        city=city,
        category=category,
        min_discount=min_discount,
        max_price=max_price,
        min_score=min_score,
        source_type=source_type,
        limit=limit,
        offset=offset,
    )
    pages = math.ceil(total_count / limit) if total_count > 0 else 1

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/lots/{lot_id}")
async def get_lot_details(
    lot_id: str,
    repo=Depends(get_repository),
) -> Dict[str, Any]:
    """Retrieve comprehensive lot profile, legal analysis, and valuation breakdown."""
    lot = repo.get_lot_by_id(lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail=f"Lot '{lot_id}' not found in Radar index")
    return lot


@router.get("/featured")
async def get_featured_deals(
    limit: int = Query(6, ge=1, le=20),
    repo=Depends(get_repository),
) -> Dict[str, Any]:
    """Retrieve top-tier auction opportunities (DealScore >= 75) for the homepage showcase."""
    items, total = repo.search_radar(min_score=75.0, min_discount=40.0, limit=limit)
    return {
        "featured": items,
        "count": len(items),
    }
