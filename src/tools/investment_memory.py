"""Investment memory database for news, thesis, and decision updates."""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class InvestmentMemory:
    def __init__(self, db_path: str = "data/investment_memory.sqlite3") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_news (
                    news_id TEXT PRIMARY KEY,
                    ticker TEXT,
                    title TEXT,
                    url TEXT,
                    source TEXT,
                    platform TEXT,
                    published_at TEXT,
                    first_seen_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_thesis (
                    ticker TEXT PRIMARY KEY,
                    thesis TEXT,
                    risk_level TEXT,
                    confidence REAL,
                    updated_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS decision_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT,
                    news_id TEXT,
                    decision TEXT,
                    reason TEXT,
                    previous_thesis TEXT,
                    new_thesis TEXT,
                    created_at TEXT
                )
            """)

    def news_id(self, title: str | None, url: str | None) -> str:
        raw = (url or title or "").strip()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def is_news_seen(self, title: str | None, url: str | None) -> bool:
        nid = self.news_id(title, url)

        with self._connect() as conn:
            row = conn.execute(
                "SELECT news_id FROM seen_news WHERE news_id = ?",
                (nid,),
            ).fetchone()

        return row is not None

    def mark_news_seen(self, ticker: str, article: dict[str, Any]) -> str:
        nid = self.news_id(article.get("title"), article.get("url"))
        now = datetime.now().isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO seen_news
                (news_id, ticker, title, url, source, platform, published_at, first_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    nid,
                    ticker,
                    article.get("title"),
                    article.get("url"),
                    article.get("source"),
                    article.get("platform"),
                    article.get("published_at") or article.get("date"),
                    now,
                ),
            )

        return nid

    def get_thesis(self, ticker: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT ticker, thesis, risk_level, confidence, updated_at
                FROM stock_thesis
                WHERE ticker = ?
                """,
                (ticker,),
            ).fetchone()

        if not row:
            return None

        return {
            "ticker": row[0],
            "thesis": row[1],
            "risk_level": row[2],
            "confidence": row[3],
            "updated_at": row[4],
        }

    def save_thesis(
        self,
        ticker: str,
        thesis: str,
        risk_level: str = "unknown",
        confidence: float = 0.0,
    ) -> None:
        now = datetime.now().isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO stock_thesis
                (ticker, thesis, risk_level, confidence, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(ticker) DO UPDATE SET
                    thesis = excluded.thesis,
                    risk_level = excluded.risk_level,
                    confidence = excluded.confidence,
                    updated_at = excluded.updated_at
                """,
                (ticker, thesis, risk_level, confidence, now),
            )

    def get_stock_thesis(self, ticker: str) -> dict[str, Any] | None:
        return self.get_thesis(ticker)

    def upsert_stock_thesis(
        self,
        ticker: str,
        thesis: str,
        risk_level: str = "unknown",
        confidence: float = 0.0,
    ) -> None:
        self.save_thesis(ticker, thesis, risk_level, confidence)

    def log_decision(
        self,
        ticker: str,
        news_id: str | None,
        decision: str,
        reason: str,
        previous_thesis: str | None,
        new_thesis: str | None,
    ) -> None:
        now = datetime.now().isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO decision_log
                (ticker, news_id, decision, reason, previous_thesis, new_thesis, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticker,
                    news_id,
                    decision,
                    reason,
                    previous_thesis,
                    new_thesis,
                    now,
                ),
            )
