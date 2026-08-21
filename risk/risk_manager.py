import math
from typing import Dict, Any, Tuple
from app_config.config_loader import ConfigLoader
from logger import logger

class PositionSizer:
    """Calculates risk-adjusted position lot sizes based on portfolio capital and stop loss width."""

    def __init__(self, lot_size: int = 25):
        self.lot_size = lot_size
        self.config = ConfigLoader()

    def calculate_lots(
        self,
        capital: float,
        entry_price: float,
        sl_points: float,
        max_risk_pct: float = 1.0,
        max_open_lots: int = 4
    ) -> int:
        if capital <= 0 or entry_price <= 0 or sl_points <= 0:
            return 0

        # Maximum allowed monetary loss for this trade
        max_risk_amount = capital * (max_risk_pct / 100.0)

        # Risk per lot (stop loss points * lot size)
        risk_per_lot = sl_points * self.lot_size

        if risk_per_lot <= 0:
            return 0

        raw_lots = max_risk_amount / risk_per_lot
        lots = math.floor(raw_lots)

        # Enforce hard limits
        lots = min(lots, max_open_lots)
        return max(1, lots) if lots >= 1 else 0

class RiskEngine:
    """Monitors capital, daily PnL, trading windows, and triggers kill switch or auto square-off."""

    def __init__(self, initial_capital: float = 500000.0):
        self.config = ConfigLoader()
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.daily_starting_capital = initial_capital
        self.max_daily_loss_pct = self.config.get("risk_management.max_daily_loss_pct", 3.0)
        self.kill_switch_active = False

    def update_pnl(self, net_pnl: float):
        self.current_capital += net_pnl
        daily_loss = self.daily_starting_capital - self.current_capital
        daily_loss_pct = (daily_loss / self.daily_starting_capital) * 100.0

        if daily_loss_pct >= self.max_daily_loss_pct:
            self.kill_switch_active = True
            logger.critical(f"KILL SWITCH ENGAGED: Daily drawdown reached {daily_loss_pct:.2f}%")

    def is_trading_allowed(self, current_time_str: str) -> Tuple[bool, str]:
        if self.kill_switch_active:
            return False, "Kill switch is ACTIVE due to daily max drawdown limit."

        # Check time window (09:15 to 14:45 for new entries)
        no_entries_after = self.config.get("trading.trading_hours.no_new_entries_after", "14:45")
        if current_time_str > no_entries_after:
            return False, f"Time limit passed ({current_time_str} > {no_entries_after}). No new entries allowed."

        return True, "Trading allowed."

    def should_force_square_off(self, current_time_str: str) -> bool:
        force_square_off_time = self.config.get("trading.trading_hours.force_square_off", "15:15")
        return current_time_str >= force_square_off_time
