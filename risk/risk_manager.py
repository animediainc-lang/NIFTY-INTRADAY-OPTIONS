from app_config.config_loader import config
from logger import logger
from datetime import datetime, time
from typing import Dict, Any

class RiskManager:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.daily_pnl = 0.0
        self.trade_count = 0

        # Risk Limits from Config
        self.max_risk_per_trade = config.get("risk.max_risk_per_trade_pct", 1.0) / 100.0
        self.max_daily_drawdown = config.get("risk.max_daily_drawdown_pct", 3.0) / 100.0
        self.max_trades_per_day = config.get("risk.max_trades_per_day", 5)
        self.shutdown_time = time(15, 15)

        self.is_shutdown = False

    def check_execution_risk(self) -> bool:
        """Checks if a new trade can be executed based on daily limits."""
        if self.is_shutdown:
            logger.warning("Risk Manager: System is shut down.")
            return False

        # 1. Check Trade Count
        if self.trade_count >= self.max_trades_per_day:
            logger.warning(f"Risk Manager: Max trades per day ({self.max_trades_per_day}) reached.")
            return False

        # 2. Check Daily Drawdown
        drawdown = abs(min(0, self.daily_pnl)) / self.initial_capital
        if drawdown >= self.max_daily_drawdown:
            logger.critical(f"Risk Manager: Daily drawdown limit ({self.max_daily_drawdown*100}%) breached. Shutting down.")
            self.is_shutdown = True
            return False

        # 3. Check Market Time
        current_time = datetime.now().time()
        if current_time >= self.shutdown_time:
            logger.warning("Risk Manager: Market closing time reached. No new trades allowed.")
            return False

        return True

    def validate_volatility(self, vix: float) -> bool:
        """Filters trades if volatility is too high (e.g., VIX > 25)."""
        max_vix = config.get("risk.max_vix", 25.0)
        if vix > max_vix:
            logger.warning(f"Risk Manager: High volatility detected (VIX: {vix}). Trade skipped.")
            return False
        return True

    def update_pnl(self, pnl: float):
        """Updates daily PnL and capital."""
        self.daily_pnl += pnl
        self.current_capital += pnl
        self.trade_count += 1
        logger.info(f"Risk Manager: Daily PnL: {self.daily_pnl:.2f}, Trades: {self.trade_count}")

    def get_max_risk_amount(self) -> float:
        """Calculates the maximum currency amount to risk on the next trade."""
        return self.current_capital * self.max_risk_per_trade

# Global Risk Manager
risk_manager = RiskManager()
