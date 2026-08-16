import logging
from datetime import datetime, time
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class RiskEngine:
    def __init__(self,
                 total_capital: float = 100000.0,
                 max_risk_per_trade_pct: float = 1.0,  # 1% per trade
                 max_daily_loss_pct: float = 3.0,      # 3% daily limit
                 max_consecutive_losses: int = 3,
                 no_new_entries_time_str: str = "14:45",
                 auto_square_off_time_str: str = "15:15",
                 lot_size: int = 25):
        self.total_capital = total_capital
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_daily_loss_limit = (max_daily_loss_pct / 100.0) * total_capital
        self.max_consecutive_losses = max_consecutive_losses
        self.lot_size = lot_size

        # Time parsing
        h, m = map(int, no_new_entries_time_str.split(":"))
        self.no_new_entries_time = time(h, m)
        h_off, m_off = map(int, auto_square_off_time_str.split(":"))
        self.auto_square_off_time = time(h_off, m_off)

        # Runtime State
        self.current_daily_loss = 0.0
        self.consecutive_losses = 0
        self.kill_switch_activated = False

    def calculate_position_size(self, entry_price: float, stop_loss_points: float) -> int:
        """Calculates lot size based on 1% total capital risk and stop loss distance"""
        if stop_loss_points <= 0 or entry_price <= 0:
            return self.lot_size # Default 1 lot

        max_risk_amount = (self.max_risk_per_trade_pct / 100.0) * self.total_capital
        risk_per_contract = stop_loss_points
        max_contracts = max_risk_amount / risk_per_contract

        # Round down to nearest Nifty lot size multiple
        lots = int(max_contracts // self.lot_size)
        if lots < 1:
            lots = 1
        return lots * self.lot_size

    def validate_new_trade(self, current_time: datetime, vix: float = 15.0) -> Tuple[bool, str]:
        """Validates all capital protection constraints before entering a trade"""
        if self.kill_switch_activated:
            return False, "Kill Switch Active: Trading halted due to risk limit breach."

        if self.current_daily_loss >= self.max_daily_loss_limit:
            self.kill_switch_activated = True
            return False, f"Daily Loss Limit Breached ({self.current_daily_loss} >= {self.max_daily_loss_limit})."

        if self.consecutive_losses >= self.max_consecutive_losses:
            self.kill_switch_activated = True
            return False, f"Consecutive Losses Limit Breached ({self.consecutive_losses} >= {self.max_consecutive_losses})."

        if current_time.time() >= self.no_new_entries_time:
            return False, f"Time constraint: No new entries after {self.no_new_entries_time}."

        if vix > 28.0:
            return False, f"India VIX elevated at {vix} > 28.0 threshold."

        return True, "Trade risk validation passed."

    def record_trade_result(self, net_pnl: float) -> None:
        """Updates internal risk trackers on trade exit"""
        if net_pnl < 0:
            self.current_daily_loss += abs(net_pnl)
            self.consecutive_losses += 1
            if self.current_daily_loss >= self.max_daily_loss_limit or self.consecutive_losses >= self.max_consecutive_losses:
                self.kill_switch_activated = True
                logger.warning("KILL SWITCH ACTIVATED due to trade result.")
        else:
            self.consecutive_losses = 0

    def is_auto_square_off_time(self, current_time: datetime) -> bool:
        """Checks if current time has reached compulsory intraday square-off at 15:15"""
        return current_time.time() >= self.auto_square_off_time
