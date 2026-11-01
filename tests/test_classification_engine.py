"""Tests for auction classification and scoring engine."""

import pytest
from leiloar.classification.engine import AuctionClassificationEngine
from leiloar.models.asset import AssetCategory
from leiloar.models.auction import AuctionLot, AuctionSourceType, AuctionStatus
from leiloar.models.classification import LiquidityTier, RiskRating


def test_classify_high_opportunity_vacant_apartment():
    lot = AuctionLot(
        lot_id="caixa_test_001",
        title="Apartamento Jardins - São Paulo/SP",
        category=AssetCategory.REAL_ESTATE_APARTMENT.value,
        source_type=AuctionSourceType.EXTRAJUDICIAL_BANK,
        status=AuctionStatus.OPEN,
        appraisal_value=1000000.00,
        minimum_bid=500000.00,
        current_discount_pct=50.0,
        occupied=False,  # Vacant!
        city="São Paulo",
        state="SP",
        url="https://leiloar.com/test",
        subrogated_debts=True,
    )

    engine = AuctionClassificationEngine()
    res = engine.classify(lot)

    assert res.opportunity_score >= 80.0
    assert res.liquidity_tier == LiquidityTier.VERY_HIGH
    assert res.risk_rating in (RiskRating.VERY_LOW, RiskRating.LOW)
    assert res.recommended_action == "BID"
    assert "50%+ Desconto" in res.tags
    assert "Desocupado" in res.tags
    assert res.estimated_net_margin_pct > 35.0


def test_classify_high_risk_non_subrogated_debt():
    lot = AuctionLot(
        lot_id="judicial_high_risk_002",
        title="Imóvel com dívidas graves",
        category=AssetCategory.REAL_ESTATE_COMMERCIAL.value,
        source_type=AuctionSourceType.JUDICIAL,
        status=AuctionStatus.OPEN,
        appraisal_value=500000.00,
        minimum_bid=400000.00,  # Only 20% discount
        current_discount_pct=20.0,
        occupied=True,
        city="Interior",
        state="SP",
        url="https://leiloar.com/test2",
        debt_condominio=150000.00,
        debt_iptu=80000.00,
        subrogated_debts=False,  # Debts NOT subrogated!
    )

    engine = AuctionClassificationEngine()
    res = engine.classify(lot)

    assert res.opportunity_score < 50.0
    assert res.recommended_action == "PASS"
    assert any(rf.code == "NON_SUBROGATED_DEBTS" for rf in res.risk_factors)
    assert res.estimated_net_margin_pct < 0  # Negative margin!
