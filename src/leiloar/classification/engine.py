"""Opportunity scoring and comprehensive classification engine for Brazilian auctions."""

from __future__ import annotations

from typing import List
from leiloar.classification.categorizer import (
    determine_liquidity_tier,
    generate_lot_tags,
)
from leiloar.classification.rules import (
    evaluate_debt_risks,
    evaluate_occupancy_risk,
)
from leiloar.models.auction import AuctionLot, AuctionSourceType
from leiloar.models.classification import (
    ClassificationResult,
    LiquidityTier,
    RiskFactor,
    RiskRating,
)


class AuctionClassificationEngine:
    """Computes investment score (DealScore), financial margins, risk rating and action recommendations."""

    def __init__(
        self,
        auctioneer_fee_pct: float = 5.0,
        itbi_tax_pct: float = 3.0,
        rgi_registry_fee_pct: float = 1.0,
        eviction_reserve_reais: float = 8000.0,
    ) -> None:
        self.auctioneer_fee_pct = auctioneer_fee_pct
        self.itbi_tax_pct = itbi_tax_pct
        self.rgi_registry_fee_pct = rgi_registry_fee_pct
        self.eviction_reserve = eviction_reserve_reais

    def calculate_deal_score(
        self,
        lot: AuctionLot,
        liquidity: LiquidityTier,
        risk_factors: List[RiskFactor],
    ) -> float:
        """Compute holistic 0-100 DealScore reflecting reward/risk balance."""
        # 1. Base Discount Component (up to 55 points)
        # 50% discount gives 50 points; 60% gives 55 points; 20% gives 20 points
        discount = max(0.0, min(70.0, lot.current_discount_pct))
        base_score = discount * 0.95

        # 2. Liquidity Bonus (up to 25 points)
        liquidity_weights = {
            LiquidityTier.VERY_HIGH: 25.0,
            LiquidityTier.HIGH: 20.0,
            LiquidityTier.MEDIUM: 14.0,
            LiquidityTier.LOW: 7.0,
            LiquidityTier.VERY_LOW: 2.0,
        }
        liquidity_bonus = liquidity_weights.get(liquidity, 12.0)

        # 3. Source Stability Bonus (up to 10 points)
        source_bonus = 10.0 if lot.source_type == AuctionSourceType.EXTRAJUDICIAL_BANK else 6.0

        # 4. Apply Risk Deductions / Boosts
        deductions = 0.0
        for rf in risk_factors:
            deductions += rf.impact_score

        # Combine
        raw_score = base_score + liquidity_bonus + source_bonus - deductions
        return round(max(0.0, min(100.0, raw_score)), 1)

    def calculate_net_margin(self, lot: AuctionLot) -> float:
        """Estimate realistic net ROI margin considering closing costs, ITBI, and eviction reserves."""
        appraisal = lot.appraisal_value
        bid = lot.minimum_bid
        if appraisal <= 0 or bid <= 0:
            return 0.0

        # Mandatory closing costs
        auctioneer_fee = bid * (self.auctioneer_fee_pct / 100.0)
        itbi_fee = bid * (self.itbi_tax_pct / 100.0)
        registry_fee = bid * (self.rgi_registry_fee_pct / 100.0)

        # Debts to be paid if non-subrogated
        extra_debts = 0.0
        if not lot.subrogated_debts:
            extra_debts = lot.debt_condominio + lot.debt_iptu

        eviction_cost = self.eviction_reserve if lot.occupied else 0.0

        total_acquisition_cost = bid + auctioneer_fee + itbi_fee + registry_fee + extra_debts + eviction_cost
        
        # Net profit vs appraisal benchmark
        estimated_profit = appraisal - total_acquisition_cost
        net_margin_pct = (estimated_profit / appraisal) * 100.0
        return round(net_margin_pct, 2)

    def determine_risk_rating(self, risk_factors: List[RiskFactor], deal_score: float) -> RiskRating:
        """Assign categorical risk tier based on identified liabilities and score."""
        danger_count = sum(1 for r in risk_factors if r.severity == "danger")
        warning_count = sum(1 for r in risk_factors if r.severity == "warning")

        if danger_count >= 2:
            return RiskRating.CRITICAL
        elif danger_count == 1:
            return RiskRating.HIGH
        elif warning_count >= 2:
            return RiskRating.MODERATE
        elif warning_count == 1:
            return RiskRating.LOW
        return RiskRating.VERY_LOW

    def classify(self, lot: AuctionLot) -> ClassificationResult:
        """Run full evaluation pipeline on an auction lot."""
        # 1. Identify risks
        risk_factors = evaluate_debt_risks(lot)
        occ_risk = evaluate_occupancy_risk(lot)
        if occ_risk:
            risk_factors.append(occ_risk)

        # 2. Determine liquidity
        liquidity = determine_liquidity_tier(lot)

        # 3. DealScore & Margins
        score = self.calculate_deal_score(lot, liquidity, risk_factors)
        net_margin = self.calculate_net_margin(lot)
        risk_rating = self.determine_risk_rating(risk_factors, score)
        tags = generate_lot_tags(lot, score)

        # 4. Recommendation & Summary
        if score >= 75.0 and risk_rating in (RiskRating.VERY_LOW, RiskRating.LOW, RiskRating.MODERATE):
            action = "BID"
            summary = (
                f"Excelente oportunidade (Score {score}/100) com desconto de {lot.current_discount_pct:.1f}% "
                f"e margem líquida estimada de {net_margin:.1f}%. Recomendada arrematação com teto definido."
            )
        elif score >= 50.0 and risk_rating != RiskRating.CRITICAL:
            action = "WATCH"
            summary = (
                f"Oportunidade moderada (Score {score}/100). Desconto de {lot.current_discount_pct:.1f}%. "
                "Acompanhar pregão e aprofundar certidões de ônus e dívidas condominiais."
            )
        else:
            action = "PASS"
            summary = (
                f"Alto risco ou margem insuficiente (Score {score}/100). "
                f"Classificação de risco: {risk_rating.value}. Não recomendado para compra imediata."
            )

        return ClassificationResult(
            lot_id=lot.lot_id,
            opportunity_score=score,
            risk_rating=risk_rating,
            liquidity_tier=liquidity,
            discount_percentage=lot.current_discount_pct,
            estimated_net_margin_pct=net_margin,
            risk_factors=risk_factors,
            tags=tags,
            summary=summary,
            recommended_action=action,
        )
