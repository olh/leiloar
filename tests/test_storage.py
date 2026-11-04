"""Tests for storage database manager and auction repository."""

from leiloar.classification.engine import AuctionClassificationEngine
from leiloar.models.asset import AssetCategory
from leiloar.models.auction import AuctionLot, AuctionSourceType, AuctionStatus
from leiloar.storage.database import DatabaseManager
from leiloar.storage.repository import AuctionRepository


def test_repository_upsert_and_search():
    db = DatabaseManager(":memory:")
    repo = AuctionRepository(db)

    lot = AuctionLot(
        lot_id="test_repo_1",
        title="Apartamento Jardins Alto Padrão",
        description="Amplo apartamento reformado",
        category=AssetCategory.REAL_ESTATE_APARTMENT.value,
        source_type=AuctionSourceType.EXTRAJUDICIAL_BANK,
        status=AuctionStatus.OPEN,
        appraisal_value=1200000.0,
        minimum_bid=600000.0,
        current_discount_pct=50.0,
        occupied=False,
        city="São Paulo",
        state="SP",
        url="https://leiloar.com/test_repo_1",
    )

    engine = AuctionClassificationEngine()
    classification = engine.classify(lot)

    repo.upsert_lot(lot, classification)

    # Search by state
    results, count = repo.search_radar(state="SP", min_discount=40.0)
    assert count == 1
    assert len(results) == 1
    assert results[0]["lot_id"] == "test_repo_1"
    assert results[0]["opportunity_score"] >= 80.0
    assert "50%+ Desconto" in results[0]["tags"]

    # Market stats
    stats = repo.get_market_statistics()
    assert stats["total_active_lots"] == 1
    assert stats["average_discount_pct"] == 50.0
    assert stats["bank_lots"] == 1
    assert stats["vacant_lots"] == 1

    db.close()
