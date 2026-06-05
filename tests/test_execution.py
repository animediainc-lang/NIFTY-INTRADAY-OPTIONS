import unittest
from unittest.mock import MagicMock, patch
from execution.trade_executor import TradeExecutor

class TestExecution(unittest.TestCase):
    def setUp(self):
        self.executor = TradeExecutor()

    @patch('execution.order_manager.order_manager.place_order')
    @patch('risk.risk_manager.risk_manager.check_execution_risk')
    @patch('risk.risk_manager.risk_manager.get_max_risk_amount')
    @patch('risk.position_sizer.position_sizer.calculate_quantity')
    def test_handle_buy(self, mock_qty, mock_risk, mock_risk_check, mock_place):
        mock_risk_check.return_value = True
        mock_risk.return_value = 1000
        mock_qty.return_value = 50
        mock_place.return_value = {"Status": 200, "Success": {"order_id": "12345"}}

        self.executor.execute_signal("BUY", "TestStrategy", "NIFTY", 100, 90)

        trade_key = "NIFTY_TestStrategy"
        self.assertIn(trade_key, self.executor.active_trades)
        self.assertEqual(self.executor.active_trades[trade_key]["quantity"], 50)

    @patch('execution.order_manager.order_manager.place_order')
    def test_target_booking(self, mock_place):
        trade_key = "TEST_Strat"
        self.executor.active_trades[trade_key] = {
            "symbol": "TEST",
            "strategy": "Strat",
            "entry_price": 100,
            "stop_loss": 90,
            "quantity": 100,
            "target_1": 110,
            "target_2": 130,
            "partial_booked": False,
            "exchange": "NFO",
            "expiry_date": "",
            "strike_price": "0",
            "right": "Call"
        }
        mock_place.return_value = {"Status": 200}

        # Price hits Target 1
        self.executor.manage_active_trades({"TEST": 115})

        self.assertTrue(self.executor.active_trades[trade_key]["partial_booked"])
        self.assertEqual(self.executor.active_trades[trade_key]["quantity"], 50)

    @patch('execution.order_manager.order_manager.get_positions')
    @patch('execution.order_manager.order_manager.place_order')
    def test_emergency_square_off(self, mock_place, mock_get_pos):
        from execution.order_manager import order_manager
        mock_get_pos.return_value = [
            {"stock_code": "NIFTY", "quantity": "50", "exchange_code": "NFO", "product_type": "options"}
        ]
        order_manager.emergency_square_off()
        mock_place.assert_called_with(
            stock_code="NIFTY", exchange_code="NFO", action="sell",
            order_type="market", quantity=50, product="options",
            expiry_date="", strike_price="0", right="others"
        )

if __name__ == "__main__":
    unittest.main()
