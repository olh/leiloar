"""Business rules and risk detection heuristics for Brazilian auction analysis."""

from __future__ import annotations

from typing import List, Optional
from leiloar.models.auction import AuctionLot, AuctionSourceType
from leiloar.models.classification import RiskFactor, RiskRating


def evaluate_debt_risks(lot: AuctionLot) -> List[RiskFactor]:
    """Analyze condominium and municipal tax liabilities against appraisal value."""
    risks: List[RiskFactor] = []
    appraisal = lot.appraisal_value or 1.0

    total_debt = lot.debt_condominio + lot.debt_iptu
    debt_ratio = (total_debt / appraisal) * 100.0

    if not lot.subrogated_debts and total_debt > 0:
        risks.append(
            RiskFactor(
                code="NON_SUBROGATED_DEBTS",
                title="Débitos não sub-rogados na arrematação",
                description=(
                    f"O edital estipula que débitos de R$ {total_debt:,.2f} correrão por conta do arrematante, "
                    f"representando {debt_ratio:.1f}% do valor de avaliação."
                ),
                severity="danger",
                impact_score=min(30.0, debt_ratio * 0.7),
                recommendation="Deduzir o valor total dos débitos do teto máximo de lance pretendido.",
            )
        )
    elif lot.debt_condominio > 0:
        risks.append(
            RiskFactor(
                code="CONDO_DEBT_MONITOR",
                title="Débitos de Condomínio em execução",
                description=(
                    f"Débito condominial de R$ {lot.debt_condominio:,.2f} objeto da lide. "
                    "Verificar se o saldo da arrematação é suficiente para cobrir integralmente o crédito exequendo."
                ),
                severity="warning" if debt_ratio > 15 else "info",
                impact_score=8.0 if debt_ratio > 15 else 3.0,
                recommendation="Conferir preferência do condomínio vs eventuais credores hipotecários nos autos.",
            )
        )

    return risks


def evaluate_occupancy_risk(lot: AuctionLot) -> Optional[RiskFactor]:
    """Assess legal costs and timeline of physical possession / eviction (imissão na posse)."""
    if lot.occupied is True:
        return RiskFactor(
            code="PROPERTY_OCCUPIED",
            title="Imóvel ocupado pelo devedor ou terceiros",
            description=(
                "Necessária expedição de mandado de imissão na posse (art. 901, § 1º CPC) ou ação de imissão de posse. "
                "Prazo médio de desocupação estimado entre 60 a 180 dias."
            ),
            severity="warning",
            impact_score=10.0,
            recommendation="Projetar custo de honorários advocatícios (R$ 5.000 - R$ 10.000) e condomínio no período.",
        )
    elif lot.occupied is False:
        return RiskFactor(
            code="PROPERTY_VACANT",
            title="Imóvel comprovadamente desocupado",
            description="Livre de moradores ou bens móveis. Posse imediata após expedição da Carta de Arrematação.",
            severity="info",
            impact_score=-10.0,  # Negative impact means positive score boost!
            recommendation="Trocar fechaduras e vistoriar o imóvel imediatamente após a homologação.",
        )
    return None
