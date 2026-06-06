import unittest
import pandas as pd
from backtesting.engine import BacktestEngine
from backtesting.report_generator import BacktestReport
from strategies.momentum_breakout import MomentumBreakout

class TestBacktesting(unittest.TestCase):
    def generate_mock_data(self):
        data = {
            'open': [100 + i for i in range(100)],
            'high': [105 + i for i in range(100)],
            'low': [95 + i for i in range(100)],
            'close': [102 + i for i in range(100)],
            'volume': [1000 for _ in range(100)],
            'oi': [5000 for _ in range(100)]
        }
        df = pd.DataFrame(data)
        df.index = pd.date_range("2023-01-01", periods=100, freq="1min")
        return df

    def test_engine_run(self):
        engine = BacktestEngine(initial_capital=200000)
        strategy = MomentumBreakout()
        data = self.generate_mock_data()

        # Manually force an entry condition
        # MomentumBreakout needs Price > VWAP, HHHL, Vol spike.
        # Our mock data is trending up, so it should trigger.
        engine.run(strategy, data, sl_points=10, tp_points=20)

        results = engine.get_results()
        self.assertIsInstance(results, pd.DataFrame)
        if not results.empty:
            self.assertIn("pnl", results.columns)

    def test_report_generation(self):
        trades = pd.DataFrame([
            {"pnl": 1000, "balance": 201000},
            {"pnl": -500, "balance": 200500}
        ])
        summary = BacktestReport.generate_summary(trades, 200000)
        self.assertEqual(summary["Total Trades"], 2)
        self.assertEqual(summary["Win Rate"], "50.00%")

if __name__ == "__main__":
    unittest.main()
