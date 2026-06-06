import unittest
import pandas as pd
from strategies.momentum_breakout import MomentumBreakout
from strategies.trend_continuation import TrendContinuation
from strategies.opening_range_breakout import OpeningRangeBreakout

class TestStrategies(unittest.TestCase):
    def generate_mock_df(self, length=30, trend="up"):
        # Frequency 1min, starting at 09:15:00
        data = {
            'timestamp': pd.date_range(start="2023-10-27 09:15:00", periods=length, freq='1min'),
            'open': [100 + i for i in range(length)],
            'high': [105 + i for i in range(length)],
            'low': [95 + i for i in range(length)],
            'close': [102 + i for i in range(length)],
            'volume': [1000 for _ in range(length)],
            'oi': [5000 + i*100 for i in range(length)]
        }
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    def test_momentum_breakout_signal(self):
        strategy = MomentumBreakout()
        df = self.generate_mock_df()
        # Force a volume spike in the last candle
        df.at[df.index[-1], 'volume'] = 5000
        strategy.update_data(df)
        self.assertTrue(strategy.check_entry())

    def test_trend_continuation_signal(self):
        strategy = TrendContinuation()
        df = self.generate_mock_df(length=50)
        # Simulate a pullback: prev price near EMA, current price breaks high
        # EMA(9) will be around 140. Let's set prev close to 140 and current to 155
        df.at[df.index[-2], 'close'] = 140
        df.at[df.index[-1], 'close'] = 155
        df.at[df.index[-1], 'high'] = 156
        df.at[df.index[-2], 'high'] = 145
        strategy.update_data(df)
        self.assertTrue(strategy.check_entry())

    def test_orb_signal(self):
        strategy = OpeningRangeBreakout(range_minutes=5)
        df = self.generate_mock_df(length=10)
        # Range (0-5 mins): High will be max of high[0:5] = 105+4 = 109
        # Last candle (index 9, 09:24:00): Close=120, Vol spike
        # range_end_time = 09:15 + 5min = 09:20.
        # current_time (09:24) > 09:20.
        df.at[df.index[-1], 'close'] = 120
        df.at[df.index[-1], 'volume'] = 5000
        strategy.update_data(df)
        self.assertTrue(strategy.check_entry())

if __name__ == "__main__":
    unittest.main()
