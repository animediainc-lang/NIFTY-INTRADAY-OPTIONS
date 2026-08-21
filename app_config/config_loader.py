import os
import re
import yaml
from typing import Any, Dict

class ConfigLoader:
    """Singleton configuration manager that loads YAML files and resolves environment variables."""
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls, config_path: str = "app_config/config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")

        with open(config_path, "r") as f:
            raw_content = f.read()

        # Resolve ${VAR} environment variables
        pattern = re.compile(r"\$\{([^}^{]+)\}")

        def replace_env_var(match):
            env_var = match.group(1)
            return os.getenv(env_var, f"MISSING_{env_var}")

        resolved_content = pattern.sub(replace_env_var, raw_content)
        self._config = yaml.safe_load(resolved_content)

    def get(self, key_path: str, default: Any = None) -> Any:
        """Fetch nested configuration value using dot notation (e.g., 'trading.symbol')."""
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
