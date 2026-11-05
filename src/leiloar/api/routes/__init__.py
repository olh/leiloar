"""API route modules."""

from leiloar.api.routes.analytics import router as analytics_router
from leiloar.api.routes.auctions import router as auctions_router

__all__ = ["auctions_router", "analytics_router"]
