import unittest
from unittest.mock import MagicMock, patch
from data.websocket_manager import WebSocketManager
from data.candle_manager import CandleManager
import pandas as pd

class TestMarketData(unittest.TestCase):
    def setUp(self):
        self.ws_manager = WebSocketManager()
        self.candle_manager = CandleManager(intervals=[1])

    def test_instrument_key(self):
        tick = {"stock_code": "NIFTY", "strike_price": "19500", "right": "Call"}
        self.assertEqual(self.candle_manager.get_instrument_key(tick), "NIFTY_19500_Call")

        spot_tick = {"stock_code": "NIFTY"}
        self.assertEqual(self.candle_manager.get_instrument_key(spot_tick), "NIFTY_0_Spot")

    def test_candle_generation(self):
        # Using 'v' for TTQ.
        ticks = [
            {"stock_code": "NIFTY", "last": 100, "v": 10, "oi": 500, "datetime": "2023-10-27 09:15:01"},
            {"stock_code": "NIFTY", "last": 110, "v": 30, "oi": 510, "datetime": "2023-10-27 09:15:30"},
            {"stock_code": "NIFTY", "last": 120, "v": 80, "oi": 600, "datetime": "2023-10-27 09:16:01"},
        ]

        for tick in ticks:
            self.candle_manager.process_tick(tick)

        key = "NIFTY_0_Spot"
        candles = self.candle_manager.get_candles(key, 1)
        self.assertIsNotNone(candles)
        self.assertEqual(len(candles), 2)
        self.assertEqual(candles.iloc[0]['high'], 110)

if __name__ == "__main__":
    unittest.main()
