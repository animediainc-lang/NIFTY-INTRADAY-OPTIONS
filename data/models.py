from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

class OptionType(str, Enum):
    CALL = "CE"
    PUT = "PE"

@dataclass
class TickData:
    symbol: str
    price: float
    quantity: int
    timestamp: datetime
    volume: int = 0
    open_interest: int = 0

@dataclass
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: int = 0

@dataclass
class OptionContract:
    symbol: str
    strike: float
    option_type: OptionType
    expiry: str
    ltp: float = 0.0
    iv: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    oi: int = 0
    change_in_oi: int = 0
    volume: int = 0

@dataclass
class OptionChain:
    timestamp: datetime
    underlying_price: float
    atm_strike: float
    contracts: Dict[str, OptionContract] = field(default_factory=dict)

    def get_contract(self, strike: float, option_type: OptionType) -> Optional[OptionContract]:
        key = f"{int(strike)}_{option_type.value}"
        return self.contracts.get(key)

@dataclass
class MarketSnapshot:
    timestamp: datetime
    underlying_price: float
    india_vix: float
    pcr: float
    max_pain: float
    atm_iv: float
    technical_indicators: Dict[str, float] = field(default_factory=dict)
    unusual_activities: List[Dict[str, Any]] = field(default_factory=list)
