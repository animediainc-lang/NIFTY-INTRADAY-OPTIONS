import pandas as pd
import sqlite3
from typing import Dict, Any, List

class DashboardDataProvider:
    def __init__(self, db_path: str = "database/trading_bot.db"):
        self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_trades(self) -> pd.DataFrame:
        """Fetches all trades from the database."""
        try:
            conn = self._get_connection()
            df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC", conn)
            conn.close()
            return df
        except Exception:
            return pd.DataFrame()

    def get_signals(self) -> pd.DataFrame:
        """Fetches all signals from the database."""
        try:
            conn = self._get_connection()
            df = pd.read_sql_query("SELECT * FROM signals ORDER BY timestamp DESC", conn)
            conn.close()
            return df
        except Exception:
            return pd.DataFrame()

    def get_daily_metrics(self) -> pd.DataFrame:
        """Fetches daily pre-market metrics."""
        try:
            conn = self._get_connection()
            df = pd.read_sql_query("SELECT * FROM daily_metrics ORDER BY date DESC", conn)
            conn.close()
            return df
        except Exception:
            return pd.DataFrame()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Calculates key performance indicators."""
        df = self.get_trades()
        if df.empty:
            return {"win_rate": 0, "total_pnl": 0, "total_trades": 0}

        # Filter closed trades for PnL analysis
        closed_trades = df[df['status'] == 'CLOSED']
        total_trades = len(closed_trades)
        wins = len(closed_trades[closed_trades['pnl'] > 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        total_pnl = closed_trades['pnl'].sum()

        return {
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "total_trades": total_trades,
            "avg_pnl": round(total_pnl / total_trades, 2) if total_trades > 0 else 0
        }

data_provider = DashboardDataProvider()
