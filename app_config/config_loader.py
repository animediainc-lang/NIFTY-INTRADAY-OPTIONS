import os
import yaml
from typing import Any, Dict, Optional
from dotenv import load_dotenv

class Config:
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            # Load environment variables from .env file if it exists
            load_dotenv()
        return cls._instance

    def load_config(self, config_path: str = "app_config/config.yaml") -> None:
        """Loads configuration from a YAML file and overrides with environment variables."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at {config_path}")

        with open(config_path, 'r') as f:
            try:
                self._config = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing YAML configuration: {e}")

        self._override_with_env(self._config)

    def _override_with_env(self, config_dict: Dict[str, Any], prefix: str = "BOT_") -> None:
        """Recursively overrides configuration values with environment variables."""
        for key, value in config_dict.items():
            env_key = f"{prefix}{key.upper()}"
            if isinstance(value, dict):
                self._override_with_env(value, f"{env_key}_")
            else:
                env_value = os.getenv(env_key)
                if env_value is not None:
                    # Try to cast to the same type as the default value
                    try:
                        if isinstance(value, bool):
                            config_dict[key] = env_value.lower() in ("true", "1", "yes")
                        elif isinstance(value, int):
                            config_dict[key] = int(env_value)
                        elif isinstance(value, float):
                            config_dict[key] = float(env_value)
                        else:
                            config_dict[key] = env_value
                    except ValueError:
                        config_dict[key] = env_value

    def get(self, key_path: str, default: Any = None) -> Any:
        """Retrieves a configuration value using a dot-separated key path."""
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

# Singleton instance for easy access
config = Config()
