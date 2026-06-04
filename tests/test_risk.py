import unittest
from risk.risk_manager import RiskManager
from datetime import time, datetime, timedelta

class TestRisk(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager(initial_capital=100000.0)
        # Reset default limits for testing
        self.rm.max_trades_per_day = 2
        self.rm.max_daily_drawdown = 0.05 # 5%

    def test_trade_count_limit(self):
        self.assertTrue(self.rm.check_execution_risk())
        self.rm.update_pnl(100)
        self.assertTrue(self.rm.check_execution_risk())
        self.rm.update_pnl(100)
        self.assertFalse(self.rm.check_execution_risk()) # Limit reached

    def test_drawdown_limit(self):
        self.assertTrue(self.rm.check_execution_risk())
        self.rm.update_pnl(-6000) # 6% loss
        self.assertFalse(self.rm.check_execution_risk())
        self.assertTrue(self.rm.is_shutdown)

    def test_time_limit(self):
        self.rm.shutdown_time = (datetime.now() - timedelta(minutes=1)).time()
        self.assertFalse(self.rm.check_execution_risk())

    def test_vix_filter(self):
        self.assertTrue(self.rm.validate_volatility(15.0))
        self.assertFalse(self.rm.validate_volatility(30.0))

if __name__ == "__main__":
    unittest.main()
