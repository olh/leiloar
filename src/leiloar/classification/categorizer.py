"""Categorization taxonomy, liquidity classification, and marketing tags."""

from __future__ import annotations

from typing import List
from leiloar.models.asset import AssetCategory
from leiloar.models.auction import AuctionLot
from leiloar.models.classification import LiquidityTier

# Tier 1 liquidity metropolitan hubs
TIER_1_CITIES = {
    "são paulo", "sao paulo", "rio de janeiro", "curitiba", "belo horizonte",
    "porto alegre", "brasília", "brasilia", "campinas", "florianópolis", "florianopolis",
}


def determine_liquidity_tier(lot: AuctionLot) -> LiquidityTier:
    """Calculate liquidity tier based on asset category, geographical market, and valuation bracket."""
    city_norm = (lot.city or "").strip().lower()
    cat = (lot.category or "").lower()

    if city_norm in TIER_1_CITIES:
        if AssetCategory.REAL_ESTATE_APARTMENT.value in cat or "apartamento" in cat:
            return LiquidityTier.VERY_HIGH
        elif AssetCategory.REAL_ESTATE_HOUSE.value in cat or "casa" in cat:
            return LiquidityTier.HIGH
        elif AssetCategory.REAL_ESTATE_COMMERCIAL.value in cat:
            return LiquidityTier.MEDIUM

    if AssetCategory.REAL_ESTATE_RURAL.value in cat or "rural" in cat or "fazenda" in cat:
        return LiquidityTier.LOW

    if AssetCategory.REAL_ESTATE_INDUSTRIAL.value in cat or "galpão" in cat:
        return LiquidityTier.LOW

    return LiquidityTier.MEDIUM


def generate_lot_tags(lot: AuctionLot, opportunity_score: float) -> List[str]:
    """Generate high-signal search and badge tags for the Radar de Leilões frontend."""
    tags: List[str] = []

    if lot.current_discount_pct >= 50.0:
        tags.append("50%+ Desconto")
    elif lot.current_discount_pct >= 40.0:
        tags.append("40%+ Desconto")

    if lot.occupied is False:
        tags.append("Desocupado")
    elif lot.occupied is True:
        tags.append("Ocupado")

    if lot.raw_metadata.get("permite_financiamento"):
        tags.append("Aceita Financiamento")

    if lot.raw_metadata.get("permite_fgts"):
        tags.append("Aceita FGTS")

    if lot.subrogated_debts:
        tags.append("Sub-rogação Fiscal")

    if opportunity_score >= 85.0:
        tags.append("Radar Ouro")
    elif opportunity_score >= 70.0:
        tags.append("Radar Destaque")

    return tags
