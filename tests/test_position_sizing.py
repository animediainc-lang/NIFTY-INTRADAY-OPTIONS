import unittest
from risk.position_sizer import PositionSizer

class TestPositionSizing(unittest.TestCase):
    def setUp(self):
        self.ps = PositionSizer(lot_size=25)

    def test_quantity_calculation(self):
        # Risk 1000, SL 10 points -> Qty 100 (4 lots)
        qty = self.ps.calculate_quantity(risk_amount=1000, entry_price=100, stop_loss=90)
        self.assertEqual(qty, 100)

    def test_rounding_down(self):
        # Risk 1000, SL 15 points -> Raw Qty 66.6 -> Round to 50 (2 lots)
        qty = self.ps.calculate_quantity(risk_amount=1000, entry_price=100, stop_loss=85)
        self.assertEqual(qty, 50)

    def test_max_exposure_limit(self):
        # Risk 5000, SL 5 points -> Qty 1000.
        # But if entry is 20000, exposure is 200,000,000.
        # Default max exposure is 500,000.
        qty = self.ps.calculate_quantity(risk_amount=5000, entry_price=20000, stop_loss=19995)
        self.assertLessEqual(qty * 20000, 500000)

    def test_margin_check(self):
        self.assertTrue(self.ps.check_margin(available_margin=100000, required_margin_per_lot=20000, qty=100))
        self.assertFalse(self.ps.check_margin(available_margin=10000, required_margin_per_lot=20000, qty=100))

if __name__ == "__main__":
    unittest.main()
