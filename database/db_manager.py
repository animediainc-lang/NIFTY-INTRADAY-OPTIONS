import os
import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from logger import logger

class DatabaseManager:
    """Manages SQLite persistence for trades, agent debates, signals, and system audits."""

    def __init__(self, db_path: str = "database/trading_system.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables for database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    pnl REAL DEFAULT 0.0,
                    slippage REAL DEFAULT 0.0,
                    total_costs REAL DEFAULT 0.0,
                    status TEXT NOT NULL, -- OPEN, CLOSED, CANCELLED
                    strategy TEXT NOT NULL,
                    mode TEXT NOT NULL -- PAPER, LIVE
                )
            """)

            # Agent debates and signal logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_debates (
                    debate_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    underlying_price REAL NOT NULL,
                    vix REAL NOT NULL,
                    pcr REAL NOT NULL,
                    tech_analysis TEXT NOT NULL,
                    greeks_analysis TEXT NOT NULL,
                    sentiment_analysis TEXT NOT NULL,
                    risk_assessment TEXT NOT NULL,
                    consensus_signal TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    vetoed_by_risk BOOLEAN NOT NULL
                )
            """)

            # Daily Performance & Audit Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summary (
                    date TEXT PRIMARY KEY,
                    starting_balance REAL NOT NULL,
                    ending_balance REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    winning_trades INTEGER NOT NULL,
                    losing_trades INTEGER NOT NULL,
                    gross_pnl REAL NOT NULL,
                    net_pnl REAL NOT NULL,
                    total_costs REAL NOT NULL
                )
            """)

            conn.commit()
            logger.info(f"Database initialized successfully at {self.db_path}")

    def log_trade(self, trade_data: Dict[str, Any]):
        """Logs trade execution entry or update."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trades
                (trade_id, timestamp, symbol, action, quantity, entry_price, exit_price, stop_loss, take_profit, pnl, slippage, total_costs, status, strategy, mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data["trade_id"],
                trade_data.get("timestamp", datetime.now().isoformat()),
                trade_data["symbol"],
                trade_data["action"],
                trade_data["quantity"],
                trade_data["entry_price"],
                trade_data.get("exit_price"),
                trade_data["stop_loss"],
                trade_data["take_profit"],
                trade_data.get("pnl", 0.0),
                trade_data.get("slippage", 0.0),
                trade_data.get("total_costs", 0.0),
                trade_data["status"],
                trade_data["strategy"],
                trade_data["mode"]
            ))
            conn.commit()

    def log_agent_debate(self, debate_data: Dict[str, Any]):
        """Logs structured multi-agent debate and reasoning output."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_debates
                (debate_id, timestamp, underlying_price, vix, pcr, tech_analysis, greeks_analysis, sentiment_analysis, risk_assessment, consensus_signal, confidence_score, vetoed_by_risk)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                debate_data["debate_id"],
                debate_data.get("timestamp", datetime.now().isoformat()),
                debate_data["underlying_price"],
                debate_data["vix"],
                debate_data["pcr"],
                json.dumps(debate_data.get("tech_analysis", {})),
                json.dumps(debate_data.get("greeks_analysis", {})),
                json.dumps(debate_data.get("sentiment_analysis", {})),
                json.dumps(debate_data.get("risk_assessment", {})),
                json.dumps(debate_data.get("consensus_signal", {})),
                debate_data.get("confidence_score", 0.0),
                debate_data.get("vetoed_by_risk", False)
            ))
            conn.commit()

    def get_recent_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
