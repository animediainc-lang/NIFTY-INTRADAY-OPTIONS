import unittest
from risk.position_sizer import PositionSizer

class TestPositionSizing(unittest.TestCase):
    def setUp(self):
        self.ps = PositionSizer(lot_size=25)

    def test_quantity_calculation(self):
        # Risk 1000, SL 10 points (Spot), is_option=True
        # Eff SL = 10 * 0.5 = 5.0
        # Qty = 1000 / 5.0 = 200 (8 lots)
        qty = self.ps.calculate_quantity(risk_amount=1000, entry_price=100, stop_loss=90, is_option=True)
        self.assertEqual(qty, 200)

    def test_rounding_down(self):
        # Risk 1000, SL 15 points, is_option=True
        # Eff SL = 15 * 0.5 = 7.5
        # Raw Qty = 1000 / 7.5 = 133.3 -> 125 (5 lots)
        qty = self.ps.calculate_quantity(risk_amount=1000, entry_price=100, stop_loss=85, is_option=True)
        self.assertEqual(qty, 125)

    def test_max_exposure_limit(self):
        qty = self.ps.calculate_quantity(risk_amount=5000, entry_price=20000, stop_loss=19995, is_option=True)
        self.assertLessEqual(qty * 20000, 500000)

    def test_margin_check(self):
        self.assertTrue(self.ps.check_margin(available_margin=100000, required_margin_per_lot=20000, qty=100))
        self.assertFalse(self.ps.check_margin(available_margin=10000, required_margin_per_lot=20000, qty=100))

if __name__ == "__main__":
    unittest.main()
