"""Database connection management and schema initialization."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class DatabaseManager:
    """Manages SQLite database connections and table lifecycle for local and edge environments."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None or db_path == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = str(Path(db_path).resolve())
        self._conn: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        """Return initialized connection with row dictionary factory."""
        if self._conn is None or self.db_path == ":memory:":
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            if self.db_path == ":memory:" and self._conn is None:
                self._conn = conn
            elif self.db_path != ":memory:":
                self._conn = conn
            self.init_schema(self._conn)
        return self._conn

    def init_schema(self, conn: sqlite3.Connection) -> None:
        """Create tables and search indexes if not present."""
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS auction_lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                source_type TEXT NOT NULL,
                status TEXT NOT NULL,
                appraisal_value REAL NOT NULL,
                minimum_bid REAL NOT NULL,
                current_discount_pct REAL NOT NULL,
                stage_1_price REAL,
                stage_2_price REAL,
                occupied INTEGER,
                address TEXT,
                neighborhood TEXT,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                postal_code TEXT,
                url TEXT NOT NULL,
                auctioneer_name TEXT NOT NULL,
                cnj_number TEXT,
                matricula TEXT,
                subrogated_debts INTEGER DEFAULT 1,
                debt_condominio REAL DEFAULT 0,
                debt_iptu REAL DEFAULT 0,
                scraped_at TEXT NOT NULL,
                raw_json TEXT
            );

            CREATE TABLE IF NOT EXISTS lot_classifications (
                lot_id TEXT PRIMARY KEY,
                opportunity_score REAL NOT NULL,
                risk_rating TEXT NOT NULL,
                liquidity_tier TEXT NOT NULL,
                discount_percentage REAL NOT NULL,
                estimated_net_margin_pct REAL NOT NULL,
                recommended_action TEXT NOT NULL,
                summary TEXT NOT NULL,
                tags_json TEXT,
                risk_factors_json TEXT,
                classified_at TEXT NOT NULL,
                FOREIGN KEY (lot_id) REFERENCES auction_lots(lot_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_lots_discount ON auction_lots(current_discount_pct DESC);
            CREATE INDEX IF NOT EXISTS idx_lots_state_city ON auction_lots(state, city);
            CREATE INDEX IF NOT EXISTS idx_lots_category ON auction_lots(category);
            CREATE INDEX IF NOT EXISTS idx_class_score ON lot_classifications(opportunity_score DESC);
            """
        )
        conn.commit()

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
