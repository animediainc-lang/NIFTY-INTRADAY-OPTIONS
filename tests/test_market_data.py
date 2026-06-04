import unittest
from unittest.mock import MagicMock, patch
from data.websocket_manager import WebSocketManager
from data.candle_manager import CandleManager
import pandas as pd

class TestMarketData(unittest.TestCase):
    def setUp(self):
        self.ws_manager = WebSocketManager()
        self.candle_manager = CandleManager(intervals=[1])

    def test_websocket_callback(self):
        mock_callback = MagicMock()
        self.ws_manager.add_callback(mock_callback)

        tick_data = {"stock_code": "NIFTY", "last": 19500, "datetime": "2023-10-27 09:15:00"}
        self.ws_manager.on_ticks(tick_data)

        mock_callback.assert_called_once_with(tick_data)

    def test_candle_generation(self):
        # Using 'v' for TTQ. CandleManager calculates delta.
        ticks = [
            {"stock_code": "NIFTY", "last": 100, "v": 10, "oi": 500, "datetime": "2023-10-27 09:15:01"},
            {"stock_code": "NIFTY", "last": 110, "v": 30, "oi": 510, "datetime": "2023-10-27 09:15:30"},
            {"stock_code": "NIFTY", "last": 105, "v": 45, "oi": 520, "datetime": "2023-10-27 09:15:59"},
            {"stock_code": "NIFTY", "last": 120, "v": 95, "oi": 600, "datetime": "2023-10-27 09:16:01"},
        ]

        for tick in ticks:
            self.candle_manager.process_tick(tick)

        candles = self.candle_manager.get_candles("NIFTY", 1)
        self.assertIsNotNone(candles)
        self.assertEqual(len(candles), 2)

        # Check first candle (09:15)
        first_candle = candles.iloc[0]
        self.assertEqual(first_candle['open'], 100)
        self.assertEqual(first_candle['high'], 110)
        self.assertEqual(first_candle['low'], 100)
        self.assertEqual(first_candle['close'], 105)
        # Ticks: (initial 10), (30-10=20), (45-30=15) -> Total delta after first tick = 35.
        # Actually, the first tick ever has delta 0 in current implementation because self.last_ttq is not yet set.
        # Let's adjust expectations or implementation.
        self.assertEqual(first_candle['volume'], 35) # 20 + 15
        self.assertEqual(first_candle['oi'], 520)

    def test_latest_closed_candle(self):
        ticks = [
            {"stock_code": "NIFTY", "last": 100, "v": 10, "oi": 500, "datetime": "2023-10-27 09:15:01"},
            {"stock_code": "NIFTY", "last": 120, "v": 30, "oi": 600, "datetime": "2023-10-27 09:16:01"},
            {"stock_code": "NIFTY", "last": 130, "v": 60, "oi": 700, "datetime": "2023-10-27 09:17:01"},
        ]
        for tick in ticks:
            self.candle_manager.process_tick(tick)

        latest = self.candle_manager.get_latest_candle("NIFTY", 1)
        self.assertIsNotNone(latest)
        self.assertEqual(latest['open'], 120)
        self.assertEqual(latest['volume'], 20) # 30 - 10

if __name__ == "__main__":
    unittest.main()
