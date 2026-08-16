from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: int = 0

@dataclass
class TickData:
    symbol: str
    timestamp: datetime
    last_price: float
    volume: int
    open_interest: int
    buy_quantity: int = 0
    sell_quantity: int = 0

@dataclass
class OptionContract:
    symbol: str               # e.g. "NIFTY24OCT24000CE"
    strike_price: float
    option_type: str          # "CE" or "PE"
    expiry: str               # "YYYY-MM-DD"
    last_price: float = 0.0
    implied_volatility: float = 0.0
    open_interest: int = 0
    oi_change: int = 0
    volume: int = 0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
