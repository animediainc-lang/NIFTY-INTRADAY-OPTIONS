from breeze_connect import BreezeConnect
from app_config.config_loader import config
from logger import logger
from typing import Dict, Any, Optional, List

class BreezeClient:
    def __init__(self):
        self.breeze: Optional[BreezeConnect] = None
        self.is_connected = False

    def _initialize_sdk(self):
        """Lazily initializes the BreezeConnect SDK with the latest config."""
        if self.breeze is None:
            api_key = config.get("breeze.api_key")
            if not api_key:
                raise ValueError("API Key missing from configuration. Call load_config() first.")
            self.breeze = BreezeConnect(api_key=api_key)

    def generate_session(self) -> bool:
        """Generates a session with the Breeze API."""
        try:
            self._initialize_sdk()
            api_secret = config.get("breeze.api_secret")
            session_token = config.get("breeze.session_token")

            if not api_secret or not session_token:
                logger.error("API Secret or Session Token missing from configuration.")
                return False

            self.breeze.generate_session(api_secret=api_secret, session_token=session_token)
            self.is_connected = True
            logger.info("Breeze session generated successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to generate Breeze session: {e}")
            self.is_connected = False
            return False

    def get_quotes(self, **kwargs) -> Dict[str, Any]:
        self._initialize_sdk()
        return self.breeze.get_quotes(**kwargs)

    def get_option_chain(self, **kwargs) -> Dict[str, Any]:
        self._initialize_sdk()
        return self.breeze.get_option_chain(**kwargs)

    def get_historical_data(self, stock_code: str, exchange_code: str, interval: str, from_date: str, to_date: str) -> Dict[str, Any]:
        self._initialize_sdk()
        interval_map = {
            "1": "1minute", "5": "5minute", "30": "30minute",
            "1m": "1minute", "5m": "5minute"
        }
        breeze_interval = interval_map.get(str(interval), interval)
        return self.breeze.get_historical_data_v2(
            interval=breeze_interval,
            from_date=from_date,
            to_date=to_date,
            stock_code=stock_code,
            exchange_code=exchange_code,
            product_type="options"
        )

# Global client
breeze_client = BreezeClient()
