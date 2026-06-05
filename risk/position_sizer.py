import math
from app_config.config_loader import config
from logger import logger
from typing import Dict, Any, Optional

class PositionSizer:
    def __init__(self, lot_size: int = 25):
        # Lot size can be overridden by config
        self._default_lot_size = lot_size

    def calculate_quantity(self, risk_amount: float, entry_price: float, stop_loss: float, is_option: bool = True) -> int:
        try:
            lot_size = config.get("trading.lot_size", self._default_lot_size)
            max_exposure = config.get("risk.max_exposure", 500000.0)

            sl_points = abs(entry_price - stop_loss)
            if sl_points == 0:
                return 0

            # Delta factor for ATM options
            effective_sl = sl_points * 0.5 if is_option else sl_points

            raw_qty = risk_amount / effective_sl
            lots = math.floor(raw_qty / lot_size)

            if lots < 1 and raw_qty >= lot_size * 0.7:
                 lots = 1

            final_qty = int(lots * lot_size)

            # Exposure Check
            exposure = final_qty * entry_price
            if exposure > max_exposure:
                final_qty = int((max_exposure // (entry_price * lot_size)) * lot_size)

            logger.info(f"Position Sizer: Final Qty: {final_qty}")
            return final_qty

        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            return 0

    def check_margin(self, available_margin: float, required_margin_per_lot: float, qty: int) -> bool:
        lot_size = config.get("trading.lot_size", self._default_lot_size)
        lots = qty / lot_size
        return (lots * required_margin_per_lot) <= available_margin

# Global Position Sizer
position_sizer = PositionSizer()
