from data.breeze_client import breeze_client
from app_config.config_loader import config
from logger import logger
from typing import List, Dict, Any, Optional

class OptionChainManager:
    def __init__(self, stock_code: str = "NIFTY"):
        self.stock_code = stock_code
        self.step = 50 # Nifty step

    def get_target_strikes(self, spot_price: float) -> Dict[str, List[float]]:
        """Identifies ATM, 1 ITM, and 1 OTM strikes."""
        atm = round(spot_price / self.step) * self.step

        return {
            "Call": [atm - self.step, atm, atm + self.step], # ITM, ATM, OTM for Calls
            "Put": [atm + self.step, atm, atm - self.step]  # ITM, ATM, OTM for Puts
        }

    def get_atm_strike(self, spot_price: float, signal_type: str) -> Optional[Dict[str, Any]]:
        """Returns the ATM strike details for a given signal."""
        atm = round(spot_price / self.step) * self.step
        # In this system, we focus on ATM by default for simplicity
        right = "Call" if "BUY" in signal_type or "LONG" in signal_type else "Put"

        return {
            "strike": float(atm),
            "right": right
        }

    def subscribe_selected_options(self, ws_manager, expiry_date: str, spot_price: float):
        """Subscribes to selected option contracts."""
        strikes = self.get_target_strikes(spot_price)

        for right, strike_list in strikes.items():
            for strike in strike_list:
                ws_manager.subscribe(
                    stock_code=self.stock_code,
                    exchange_code="NFO",
                    product_type="options",
                    expiry_date=expiry_date,
                    strike_price=str(strike),
                    right=right
                )
                logger.info(f"Subscribed to {self.stock_code} {expiry_date} {strike} {right}")

option_manager = OptionChainManager()
