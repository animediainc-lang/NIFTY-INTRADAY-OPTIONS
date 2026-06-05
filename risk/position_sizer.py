import math
from app_config.config_loader import config
from logger import logger
from typing import Dict, Any, Optional

class PositionSizer:
    def __init__(self, lot_size: int = 25):
        self.lot_size = lot_size # Nifty default
        self.max_exposure = config.get("risk.max_exposure", 500000.0)

    def calculate_quantity(self, risk_amount: float, entry_price: float, stop_loss: float) -> int:
        """
        Calculates the number of units (quantity) based on fixed risk amount.
        Risk = (Entry - SL) * Quantity
        Quantity = Risk / (Entry - SL)
        """
        try:
            sl_points = abs(entry_price - stop_loss)
            if sl_points == 0:
                logger.warning("Stop loss points are zero. Cannot calculate quantity.")
                return 0

            raw_qty = risk_amount / sl_points

            # Round down to nearest multiple of lot size
            lots = math.floor(raw_qty / self.lot_size)

            # Minimum 1 lot if raw_qty allows it
            if lots < 1 and raw_qty >= self.lot_size * 0.8: # Allow small buffer
                 lots = 1

            final_qty = int(lots * self.lot_size)

            # Exposure Check
            exposure = final_qty * entry_price
            if exposure > self.max_exposure:
                logger.warning(f"Calculated exposure ({exposure}) exceeds max exposure ({self.max_exposure}). Reducing qty.")
                final_qty = int((self.max_exposure // (entry_price * self.lot_size)) * self.lot_size)

            logger.info(f"Position Sizer: Risk: {risk_amount}, SL Points: {sl_points}, Final Qty: {final_qty} ({lots} lots)")
            return final_qty

        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            return 0

    def check_margin(self, available_margin: float, required_margin_per_lot: float, qty: int) -> bool:
        """Verifies if enough margin is available for the trade."""
        lots = qty / self.lot_size
        total_required = lots * required_margin_per_lot

        if total_required > available_margin:
            logger.warning(f"Insufficient margin. Required: {total_required}, Available: {available_margin}")
            return False
        return True

# Global Position Sizer
position_sizer = PositionSizer()
