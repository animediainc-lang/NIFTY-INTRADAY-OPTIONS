import yaml
import os
from threading import Lock
from pathlib import Path
from typing import Any, Dict, Optional, Union

class Config:
    _instance: Optional['Config'] = None
    _lock: Lock = Lock()
    _config_data: Dict[str, Any]
    project_root: Path

    def __new__(cls) -> 'Config':
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Config, cls).__new__(cls)
                cls._instance._config_data = {}
                # Set project root relative to this file
                cls._instance.project_root = Path(__file__).parent.parent
                cls._instance.load_config()
        return cls._instance

    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> None:
        if config_path is None:
            resolved_path = self.project_root / "config" / "config.yml"
        else:
            resolved_path = Path(config_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {resolved_path}")

        with open(resolved_path, 'r') as file:
            try:
                self._config_data = yaml.safe_load(file) or {}
            except yaml.YAMLError as exc:
                raise ValueError(f"Error parsing YAML configuration: {exc}")

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def reset(self) -> None:
        """Reset config for testing purposes"""
        self._config_data = {}

# Singleton accessor
def get_config() -> Config:
    return Config()
