import unittest
from unittest.mock import MagicMock, patch
from data.pre_market_analyzer import PreMarketAnalyzer
import pandas as pd

class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.analyzer = PreMarketAnalyzer(stock_code="NIFTY")

    @patch('data.breeze_client.breeze_client.get_historical_data')
    def test_calculate_pdl_pdh(self, mock_get_hist):
        mock_get_hist.return_value = {
            "Status": 200,
            "Success": [
                {"high": 20000, "low": 19000, "close": 19500}
            ]
        }
        metrics = self.analyzer.calculate_pdl_pdh()
        self.assertEqual(metrics["pdh"], 20000)
        self.assertEqual(metrics["pdl"], 19000)

    @patch('data.breeze_client.breeze_client.get_option_chain')
    def test_option_chain_metrics(self, mock_get_oc):
        mock_get_oc.return_value = {
            "Status": 200,
            "Success": [
                {"right": "Call", "strike_price": 19000, "open_interest": 100},
                {"right": "Call", "strike_price": 19500, "open_interest": 200},
                {"right": "Put", "strike_price": 19000, "open_interest": 300},
                {"right": "Put", "strike_price": 19500, "open_interest": 150},
            ]
        }
        metrics = self.analyzer.get_option_chain_metrics("2023-11-02T00:00:00.000Z")
        self.assertEqual(metrics["pcr"], 1.5)
        self.assertIn("max_pain", metrics)

    def test_max_pain_logic(self):
        # Manual test for Max Pain logic
        # Strikes: 100, 200
        # Call OI: 100@100, 50@200
        # Put OI: 50@100, 100@200
        data = [
            {"right": "Call", "strike_price": 100, "open_interest": 100},
            {"right": "Call", "strike_price": 200, "open_interest": 50},
            {"right": "Put", "strike_price": 100, "open_interest": 50},
            {"right": "Put", "strike_price": 200, "open_interest": 100},
        ]
        with patch('data.breeze_client.breeze_client.get_option_chain') as mock_oc:
            mock_oc.return_value = {"Status": 200, "Success": data}
            metrics = self.analyzer.get_option_chain_metrics("expiry")

            # If Spot=100:
            # Call Pain: (100-100)*100 + (100-200)*50 (but only if Spot > Strike) -> 0
            # Put Pain: (100-100)*50 + (200-100)*100 -> 10000
            # Total Pain @ 100 = 10000

            # If Spot=200:
            # Call Pain: (200-100)*100 + (200-200)*50 -> 10000
            # Put Pain: (100-200)*50 + (200-200)*100 -> 0
            # Total Pain @ 200 = 10000

            self.assertIn(metrics["max_pain"], [100, 200])

if __name__ == "__main__":
    unittest.main()
