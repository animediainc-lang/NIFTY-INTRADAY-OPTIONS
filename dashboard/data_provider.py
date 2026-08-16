from typing import Dict, Any, List
from datetime import datetime

class DashboardDataProvider:
    """Aggregates system state, agent debate logs, active positions, and PnL for dashboard rendering"""
    def __init__(self):
        self.trading_mode = "PAPER"
        self.capital = 100000.0
        self.net_pnl = 0.0
        self.active_positions: List[Dict[str, Any]] = []
        self.closed_trades: List[Dict[str, Any]] = []
        self.recent_debate_logs: List[Dict[str, Any]] = []
        self.risk_status = {"kill_switch": False, "consecutive_losses": 0, "daily_loss": 0.0}

    def update_state(self, capital: float, net_pnl: float, positions: List[Dict[str, Any]],
                     closed_trades: List[Dict[str, Any]], debate_log: Dict[str, Any], risk_state: Dict[str, Any]) -> None:
        self.capital = capital
        self.net_pnl = net_pnl
        self.active_positions = positions
        self.closed_trades = closed_trades
        if debate_log:
            self.recent_debate_logs.insert(0, debate_log)
            if len(self.recent_debate_logs) > 20:
                self.recent_debate_logs.pop()
        self.risk_status = risk_state

    def get_summary_metrics(self) -> Dict[str, Any]:
        return {
            "trading_mode": self.trading_mode,
            "total_capital": round(self.capital, 2),
            "net_pnl": round(self.net_pnl, 2),
            "active_positions_count": len(self.active_positions),
            "closed_trades_count": len(self.closed_trades),
            "kill_switch": self.risk_status.get("kill_switch", False)
        }
