"""Data repository for querying, indexing and persisting radar auction items."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from leiloar.models.auction import AuctionLot, AuctionSourceType, AuctionStatus, LegalProcess
from leiloar.models.classification import ClassificationResult, LiquidityTier, RiskRating
from leiloar.storage.database import DatabaseManager


class AuctionRepository:
    """High-level repository for Leiloar Radar database operations."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def upsert_lot(self, lot: AuctionLot, classification: Optional[ClassificationResult] = None) -> None:
        """Store or update an auction lot along with its AI/rules classification."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cnj = lot.legal_process.cnj_number if lot.legal_process else None
        now_iso = datetime.now(timezone.utc).isoformat()

        cursor.execute(
            """
            INSERT INTO auction_lots (
                lot_id, title, description, category, source_type, status,
                appraisal_value, minimum_bid, current_discount_pct,
                stage_1_price, stage_2_price, occupied, address, neighborhood,
                city, state, postal_code, url, auctioneer_name, cnj_number,
                matricula, subrogated_debts, debt_condominio, debt_iptu,
                scraped_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(lot_id) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                minimum_bid=excluded.minimum_bid,
                current_discount_pct=excluded.current_discount_pct,
                stage_1_price=excluded.stage_1_price,
                stage_2_price=excluded.stage_2_price,
                occupied=excluded.occupied,
                debt_condominio=excluded.debt_condominio,
                debt_iptu=excluded.debt_iptu,
                scraped_at=excluded.scraped_at,
                raw_json=excluded.raw_json
            """,
            (
                lot.lot_id,
                lot.title,
                lot.description,
                lot.category,
                lot.source_type.value if hasattr(lot.source_type, "value") else str(lot.source_type),
                lot.status.value if hasattr(lot.status, "value") else str(lot.status),
                lot.appraisal_value,
                lot.minimum_bid,
                lot.current_discount_pct,
                lot.stage_1_price,
                lot.stage_2_price,
                1 if lot.occupied is True else (0 if lot.occupied is False else None),
                lot.address,
                lot.neighborhood,
                lot.city,
                lot.state,
                lot.postal_code,
                lot.url,
                lot.auctioneer_name,
                cnj,
                lot.matricula,
                1 if lot.subrogated_debts else 0,
                lot.debt_condominio,
                lot.debt_iptu,
                lot.scraped_at.isoformat() if lot.scraped_at else now_iso,
                json.dumps(lot.raw_metadata),
            ),
        )

        if classification:
            cursor.execute(
                """
                INSERT INTO lot_classifications (
                    lot_id, opportunity_score, risk_rating, liquidity_tier,
                    discount_percentage, estimated_net_margin_pct,
                    recommended_action, summary, tags_json, risk_factors_json, classified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lot_id) DO UPDATE SET
                    opportunity_score=excluded.opportunity_score,
                    risk_rating=excluded.risk_rating,
                    liquidity_tier=excluded.liquidity_tier,
                    discount_percentage=excluded.discount_percentage,
                    estimated_net_margin_pct=excluded.estimated_net_margin_pct,
                    recommended_action=excluded.recommended_action,
                    summary=excluded.summary,
                    tags_json=excluded.tags_json,
                    risk_factors_json=excluded.risk_factors_json,
                    classified_at=excluded.classified_at
                """,
                (
                    classification.lot_id,
                    classification.opportunity_score,
                    classification.risk_rating.value if hasattr(classification.risk_rating, "value") else str(classification.risk_rating),
                    classification.liquidity_tier.value if hasattr(classification.liquidity_tier, "value") else str(classification.liquidity_tier),
                    classification.discount_percentage,
                    classification.estimated_net_margin_pct,
                    classification.recommended_action,
                    classification.summary,
                    json.dumps(classification.tags),
                    json.dumps([rf.model_dump() for rf in classification.risk_factors]),
                    now_iso,
                ),
            )

        conn.commit()

    def get_lot_by_id(self, lot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single lot record with classification by primary ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        select_sql = """
            SELECT 
                l.*,
                c.opportunity_score,
                c.risk_rating,
                c.liquidity_tier,
                c.estimated_net_margin_pct,
                c.recommended_action,
                c.summary,
                c.tags_json,
                c.risk_factors_json
            FROM auction_lots l
            LEFT JOIN lot_classifications c ON l.lot_id = c.lot_id
            WHERE l.lot_id = ?
        """
        cursor.execute(select_sql, [lot_id])
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["tags"] = json.loads(d["tags_json"]) if d.get("tags_json") else []
        d["risk_factors"] = json.loads(d["risk_factors_json"]) if d.get("risk_factors_json") else []
        return d

    def search_radar(
        self,
        query: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        category: Optional[str] = None,
        min_discount: Optional[float] = None,
        max_price: Optional[float] = None,
        min_score: Optional[float] = None,
        source_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Execute faceted search matching Leiloar Radar user filters."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        where_clauses: List[str] = []
        params: List[Any] = []

        if query:
            where_clauses.append("(l.title LIKE ? OR l.description LIKE ? OR l.city LIKE ?)")
            q = f"%{query}%"
            params.extend([q, q, q])

        if state:
            where_clauses.append("l.state = ?")
            params.append(state.upper())

        if city:
            where_clauses.append("l.city LIKE ?")
            params.append(f"%{city}%")

        if category:
            where_clauses.append("l.category = ?")
            params.append(category)

        if min_discount is not None:
            where_clauses.append("l.current_discount_pct >= ?")
            params.append(min_discount)

        if max_price is not None:
            where_clauses.append("l.minimum_bid <= ?")
            params.append(max_price)

        if source_type:
            where_clauses.append("l.source_type = ?")
            params.append(source_type)

        if min_score is not None:
            where_clauses.append("c.opportunity_score >= ?")
            params.append(min_score)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Count total
        count_sql = f"""
            SELECT COUNT(*) as cnt
            FROM auction_lots l
            LEFT JOIN lot_classifications c ON l.lot_id = c.lot_id
            {where_sql}
        """
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()["cnt"]

        # Fetch records
        select_sql = f"""
            SELECT 
                l.*,
                c.opportunity_score,
                c.risk_rating,
                c.liquidity_tier,
                c.estimated_net_margin_pct,
                c.recommended_action,
                c.summary,
                c.tags_json
            FROM auction_lots l
            LEFT JOIN lot_classifications c ON l.lot_id = c.lot_id
            {where_sql}
            ORDER BY COALESCE(c.opportunity_score, 0) DESC, l.current_discount_pct DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(select_sql, params + [limit, offset])
        rows = cursor.fetchall()

        results: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            if d.get("tags_json"):
                d["tags"] = json.loads(d["tags_json"])
            else:
                d["tags"] = []
            results.append(d)

        return results, total_count

    def get_market_statistics(self) -> Dict[str, Any]:
        """Aggregate high-level metrics for dashboard cards and radar analytics."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_lots,
                COALESCE(AVG(current_discount_pct), 0) as avg_discount,
                COALESCE(SUM(appraisal_value), 0) as total_appraisal_volume,
                COALESCE(SUM(minimum_bid), 0) as total_bid_volume,
                SUM(CASE WHEN source_type = 'judicial' THEN 1 ELSE 0 END) as judicial_count,
                SUM(CASE WHEN source_type LIKE '%bank%' THEN 1 ELSE 0 END) as bank_count,
                SUM(CASE WHEN occupied = 0 THEN 1 ELSE 0 END) as vacant_count
            FROM auction_lots
            """
        )
        row = dict(cursor.fetchone())

        cursor.execute(
            """
            SELECT state, COUNT(*) as lot_count, AVG(current_discount_pct) as avg_discount
            FROM auction_lots
            GROUP BY state
            ORDER BY lot_count DESC
            LIMIT 5
            """
        )
        top_states = [dict(r) for r in cursor.fetchall()]

        return {
            "total_active_lots": row["total_lots"],
            "average_discount_pct": round(row["avg_discount"], 2),
            "total_appraisal_volume_brl": round(row["total_appraisal_volume"], 2),
            "total_bid_volume_brl": round(row["total_bid_volume"], 2),
            "judicial_lots": row["judicial_count"],
            "bank_lots": row["bank_count"],
            "vacant_lots": row["vacant_count"],
            "top_states": top_states,
        }
