"""Domain models for auction classification, risk assessment, and deal scoring."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskRating(str, Enum):
    """Aggregate legal and economic risk tier."""
    VERY_LOW = "A_VERY_LOW"      # Safe extrajudicial, vacant, cleared title
    LOW = "B_LOW"                # Judicial execution with clean debts or clear subrogation
    MODERATE = "C_MODERATE"      # Occupied property, manageable eviction timeline
    HIGH = "D_HIGH"              # Pending third-party appeals or unquantified liabilities
    CRITICAL = "E_CRITICAL"      # Usufruct, family asset claims, or bankrupt company burdens


class LiquidityTier(str, Enum):
    """Estimated resale/market liquidity."""
    VERY_HIGH = "muito_alta"    # 1-2 bedroom apartments in prime metropolitan hubs
    HIGH = "alta"                # Standard residential in capital cities
    MEDIUM = "media"             # Commercial suites or outer metropolitan units
    LOW = "baixa"                # Large industrial warehouses or remote rural plots
    VERY_LOW = "muito_baixa"    # Complex judicial fractions or non-delimited land shares


class RiskFactor(BaseModel):
    """Specific risk factor identified during analysis."""
    code: str = Field(..., description="Unique risk identifier (e.g. COND_DEBT_HIGH)")
    title: str = Field(..., description="Short risk title")
    description: str = Field(..., description="Detailed explanation of legal/economic hazard")
    severity: str = Field(default="warning", description="info, warning, or danger")
    impact_score: float = Field(default=0.0, description="Deduction applied to DealScore")
    recommendation: Optional[str] = Field(default=None, description="Suggested due diligence countermeasure")


class ClassificationResult(BaseModel):
    """Unified classification and investment profile calculated for an auction lot."""
    lot_id: str
    opportunity_score: float = Field(
        ..., ge=0.0, le=100.0,
        description="Global DealScore (0 to 100), combining discount, risks, and liquidity"
    )
    risk_rating: RiskRating
    liquidity_tier: LiquidityTier
    discount_percentage: float = Field(..., description="Effective discount vs market/appraisal")
    estimated_net_margin_pct: float = Field(
        ..., description="Estimated net profit margin after legal fees, transfer taxes (ITBI), and debts"
    )
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list, description="Categorical tags (e.g. '50%+ Desconto', 'Desocupado')")
    summary: str = Field(..., description="Executive verdict and due diligence synopsis")
    recommended_action: str = Field(..., description="Actionable guideline: 'BID', 'WATCH', or 'PASS'")
