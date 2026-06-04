from data.breeze_client import breeze_client
from app_config.config_loader import config
from logger import logger
from typing import List, Dict, Any

class OptionChainManager:
    def __init__(self, stock_code: str = "NIFTY"):
        self.stock_code = stock_code

    def get_target_strikes(self, spot_price: float, step: int = 50) -> Dict[str, List[float]]:
        """Identifies ATM, 1 ITM, and 1 OTM strikes."""
        atm = round(spot_price / step) * step

        return {
            "CE": [atm - step, atm, atm + step], # ITM, ATM, OTM for Calls
            "PE": [atm + step, atm, atm - step]  # ITM, ATM, OTM for Puts
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
