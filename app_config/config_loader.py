import os
import yaml
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

class ConfigLoader:
    _instance = None

    def __new__(cls, config_path: str = "app_config/config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path: str) -> None:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at {config_path}")

        with open(config_path, "r") as f:
            self._config: Dict[str, Any] = yaml.safe_load(f)

        # Process environment variable overrides
        self._override_from_env()

    def _override_from_env(self) -> None:
        if os.getenv("KITE_API_KEY"):
            self._config["broker"]["api_key"] = os.getenv("KITE_API_KEY")
        if os.getenv("KITE_API_SECRET"):
            self._config["broker"]["api_secret"] = os.getenv("KITE_API_SECRET")
        if os.getenv("KITE_ACCESS_TOKEN"):
            self._config["broker"]["access_token"] = os.getenv("KITE_ACCESS_TOKEN")
        if os.getenv("ANTHROPIC_API_KEY"):
            self._config["llm"]["api_key"] = os.getenv("ANTHROPIC_API_KEY")
        if os.getenv("BOT_TRADING_MODE"):
            self._config["trading"]["mode"] = os.getenv("BOT_TRADING_MODE")
        if os.getenv("BOT_TRADING_CAPITAL"):
            self._config["trading"]["capital"] = float(os.getenv("BOT_TRADING_CAPITAL"))

    def get(self, key_path: str, default: Any = None) -> Any:
        """Fetch nested configuration setting via dot notation (e.g. 'trading.capital')"""
        keys = key_path.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    @property
    def config(self) -> Dict[str, Any]:
        return self._config
