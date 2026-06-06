import unittest
from unittest.mock import patch, MagicMock
from execution.order_manager import OrderManager
from app_config.config_loader import config

class TestPaperTrading(unittest.TestCase):
    def setUp(self):
        self.om = OrderManager()

    @patch('data.breeze_client.breeze_client._initialize_sdk')
    def test_paper_mode_bypasses_api(self, mock_init):
        # We must use a mock for the 'breeze' attribute itself since it's None initially
        from data.breeze_client import breeze_client
        breeze_client.breeze = MagicMock()

        config._config["trading"] = {"mode": "paper"}

        response = self.om.place_order(
            stock_code="NIFTY", exchange_code="NFO", action="buy",
            order_type="market", quantity=50
        )

        self.assertEqual(response["Status"], 200)
        self.assertTrue(response["Success"]["order_id"].startswith("PAPER_"))
        # In paper mode, breeze.place_order should NOT be called
        breeze_client.breeze.place_order.assert_not_called()

    @patch('data.breeze_client.breeze_client._initialize_sdk')
    def test_live_mode_calls_api(self, mock_init):
        from data.breeze_client import breeze_client
        breeze_client.breeze = MagicMock()

        config._config["trading"] = {"mode": "live"}
        breeze_client.breeze.place_order.return_value = {"Status": 200, "Success": {"order_id": "LIVE_123"}}

        response = self.om.place_order(
            stock_code="NIFTY", exchange_code="NFO", action="buy",
            order_type="market", quantity=50
        )

        self.assertEqual(response["Success"]["order_id"], "LIVE_123")
        breeze_client.breeze.place_order.assert_called_once()

if __name__ == "__main__":
    unittest.main()
