import sqlite3
import os
from logger import logger
from datetime import datetime
from typing import Dict, Any, List

class DatabaseManager:
    def __init__(self, db_path: str = "database/trading_bot.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initializes the database schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self._get_connection()
        cursor = conn.cursor()

        # Trades Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT,
                strategy TEXT,
                action TEXT,
                entry_price REAL,
                exit_price REAL,
                quantity INTEGER,
                pnl REAL,
                status TEXT
            )
        ''')

        # Signals Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT,
                strategy TEXT,
                signal_type TEXT,
                price REAL,
                ai_score REAL
            )
        ''')

        # Daily Metrics Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_metrics (
                date DATE PRIMARY KEY,
                pcr REAL,
                vix REAL,
                max_pain REAL,
                pdh REAL,
                pdl REAL
            )
        ''')

        conn.commit()
        conn.close()

    def log_trade(self, symbol: str, strategy: str, action: str, price: float, quantity: int, pnl: float = 0, status: str = "OPEN"):
        """Logs a trade entry or exit."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trades (symbol, strategy, action, entry_price, quantity, pnl, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, strategy, action, price, quantity, pnl, status))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB Error logging trade: {e}")

    def log_signal(self, symbol: str, strategy: str, signal_type: str, price: float, ai_score: float):
        """Logs a strategy signal."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO signals (symbol, strategy, signal_type, price, ai_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, strategy, signal_type, price, ai_score))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB Error logging signal: {e}")

    def log_daily_metrics(self, metrics: Dict[str, Any]):
        """Logs pre-market metrics for the day."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            date_str = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('''
                INSERT OR REPLACE INTO daily_metrics (date, pcr, vix, max_pain, pdh, pdl)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (date_str, metrics.get("pcr"), metrics.get("vix"), metrics.get("max_pain"), metrics.get("pdh"), metrics.get("pdl")))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB Error logging daily metrics: {e}")

# Global Database Manager
db_manager = DatabaseManager()
