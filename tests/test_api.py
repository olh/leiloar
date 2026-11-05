"""Integration tests for FastAPI endpoints powering leiloar.com/radar-leiloes."""

import pytest
from fastapi.testclient import TestClient
from leiloar.api import create_app
from leiloar.classification.engine import AuctionClassificationEngine
from leiloar.models.asset import AssetCategory
from leiloar.models.auction import AuctionLot, AuctionSourceType, AuctionStatus


@pytest.fixture
def test_client():
    app = create_app(":memory:")
    client = TestClient(app)

    # Seed test lots
    repo = app.state.repository
    engine = AuctionClassificationEngine()

    lot1 = AuctionLot(
        lot_id="api_test_01",
        title="Apartamento Moema Premium",
        description="Cobertura duplex com vista panorâmica",
        category=AssetCategory.REAL_ESTATE_APARTMENT.value,
        source_type=AuctionSourceType.EXTRAJUDICIAL_BANK,
        status=AuctionStatus.OPEN,
        appraisal_value=2000000.0,
        minimum_bid=1000000.0,
        current_discount_pct=50.0,
        occupied=False,
        city="São Paulo",
        state="SP",
        url="https://leiloar.com/radar/api_test_01",
    )
    classification1 = engine.classify(lot1)
    repo.upsert_lot(lot1, classification1)

    lot2 = AuctionLot(
        lot_id="api_test_02",
        title="Casa Barra da Tijuca",
        description="Casa em condomínio de luxo",
        category=AssetCategory.REAL_ESTATE_HOUSE.value,
        source_type=AuctionSourceType.JUDICIAL,
        status=AuctionStatus.OPEN,
        appraisal_value=1500000.0,
        minimum_bid=1050000.0,
        current_discount_pct=30.0,
        occupied=True,
        city="Rio de Janeiro",
        state="RJ",
        url="https://leiloar.com/radar/api_test_02",
    )
    classification2 = engine.classify(lot2)
    repo.upsert_lot(lot2, classification2)

    return client


def test_health_check(test_client):
    res = test_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "leiloar-radar-api"


def test_list_radar_lots(test_client):
    res = test_client.get("/api/v1/radar/lots")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["lot_id"] == "api_test_01"  # Higher score sorted first


def test_filter_radar_by_state_and_discount(test_client):
    res = test_client.get("/api/v1/radar/lots?state=SP&min_discount=40")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["state"] == "SP"
    assert data["items"][0]["current_discount_pct"] >= 40.0


def test_get_featured_deals(test_client):
    res = test_client.get("/api/v1/radar/featured")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 1
    assert data["featured"][0]["opportunity_score"] >= 75.0


def test_get_market_statistics(test_client):
    res = test_client.get("/api/v1/radar/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_active_lots"] == 2
    assert data["average_discount_pct"] == 40.0
    assert data["judicial_lots"] == 1
    assert data["bank_lots"] == 1


def test_get_lot_details_success_and_404(test_client):
    res_ok = test_client.get("/api/v1/radar/lots/api_test_01")
    assert res_ok.status_code == 200
    assert res_ok.json()["lot_id"] == "api_test_01"

    res_404 = test_client.get("/api/v1/radar/lots/nonexistent_lot_xyz")
    assert res_404.status_code == 404
