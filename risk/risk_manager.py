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
        self.is_shutdown = False

    def _get_limit(self, key: str, default: Any) -> Any:
        return config.get(key, default)

    def check_execution_risk(self) -> bool:
        if self.is_shutdown:
            logger.warning("Risk Manager: System is shut down.")
            return False

        max_trades = self._get_limit("risk.max_trades_per_day", 5)
        if self.trade_count >= max_trades:
            logger.warning(f"Risk Manager: Max trades reached ({max_trades}).")
            return False

        max_dd_pct = self._get_limit("risk.max_daily_drawdown_pct", 3.0) / 100.0
        drawdown = abs(min(0, self.daily_pnl)) / self.initial_capital
        if drawdown >= max_dd_pct:
            logger.critical(f"Risk Manager: Daily drawdown limit ({max_dd_pct*100}%) breached.")
            self.is_shutdown = True
            return False

        current_time = datetime.now().time()
        shutdown_time_str = self._get_limit("risk.shutdown_time", "15:15")
        shutdown_time = datetime.strptime(shutdown_time_str, "%H:%M").time()
        if current_time >= shutdown_time:
            logger.warning("Risk Manager: Market closing time reached.")
            return False

        return True

    def validate_volatility(self, vix: float) -> bool:
        max_vix = self._get_limit("risk.max_vix", 25.0)
        return vix <= max_vix

    def update_pnl(self, pnl: float):
        self.daily_pnl += pnl
        self.current_capital += pnl
        self.trade_count += 1
        logger.info(f"Risk Manager: Updated Daily PnL: {self.daily_pnl:.2f}")

    def get_max_risk_amount(self) -> float:
        risk_pct = self._get_limit("risk.max_risk_per_trade_pct", 1.0) / 100.0
        return self.current_capital * risk_pct

# Global Risk Manager
risk_manager = RiskManager()
