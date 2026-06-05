import unittest
from risk.risk_manager import RiskManager
from app_config.config_loader import config
from datetime import time, datetime, timedelta

class TestRisk(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager(initial_capital=100000.0)
        # Manually override config values for testing to avoid race with global config
        config._config["risk"] = {
            "max_trades_per_day": 2,
            "max_daily_drawdown_pct": 5.0,
            "shutdown_time": (datetime.now() + timedelta(hours=1)).strftime("%H:%M"),
            "max_risk_per_trade_pct": 1.0
        }

    def test_trade_count_limit(self):
        self.assertTrue(self.rm.check_execution_risk())
        self.rm.update_pnl(100)
        self.assertTrue(self.rm.check_execution_risk())
        self.rm.update_pnl(100)
        self.assertFalse(self.rm.check_execution_risk())

    def test_drawdown_limit(self):
        self.assertTrue(self.rm.check_execution_risk())
        self.rm.update_pnl(-6000) # 6% loss
        self.assertFalse(self.rm.check_execution_risk())
        self.assertTrue(self.rm.is_shutdown)

    def test_time_limit(self):
        config._config["risk"]["shutdown_time"] = (datetime.now() - timedelta(minutes=1)).strftime("%H:%M")
        self.assertFalse(self.rm.check_execution_risk())

    def test_vix_filter(self):
        config._config["risk"]["max_vix"] = 25.0
        self.assertTrue(self.rm.validate_volatility(15.0))
        self.assertFalse(self.rm.validate_volatility(30.0))

if __name__ == "__main__":
    unittest.main()
