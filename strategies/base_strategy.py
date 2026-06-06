from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.data: Optional[pd.DataFrame] = None
        self.parameters: Dict[str, Any] = {}

    def update_data(self, df: pd.DataFrame):
        """Updates the internal dataframe with new OHLC data."""
        self.data = df

    @abstractmethod
    def check_entry(self) -> bool:
        """Checks if entry conditions are met."""
        pass

    @abstractmethod
    def check_exit(self) -> bool:
        """Checks if exit conditions are met."""
        pass

    def get_signal(self) -> Optional[str]:
        """Returns 'BUY', 'SELL', or None."""
        if self.check_entry():
            return "BUY"
        elif self.check_exit():
            return "SELL"
        return None
