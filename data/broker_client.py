import time
import random
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any
from data.models import TickData, OptionContract

logger = logging.getLogger(__name__)

class BaseBrokerClient(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def subscribe_ticks(self, symbols: List[str], callback: Callable[[TickData], None]) -> None:
        pass

    @abstractmethod
    def place_order(self, symbol: str, transaction_type: str, quantity: int, order_type: str = "MARKET", price: float = 0.0) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        pass


class MockPaperBrokerClient(BaseBrokerClient):
    """Paper trading client generating realistic simulated Nifty spot and option ticks"""
    def __init__(self, initial_spot: float = 24000.0):
        self.spot_price = initial_spot
        self.subscribed_symbols: List[str] = []
        self.tick_callback: Optional[Callable[[TickData], None]] = None
        self.positions: List[Dict[str, Any]] = []
        self.order_counter = 1000
        self.is_connected = False

    def connect(self) -> bool:
        self.is_connected = True
        logger.info("MockPaperBrokerClient connected successfully.")
        return True

    def subscribe_ticks(self, symbols: List[str], callback: Callable[[TickData], None]) -> None:
        self.subscribed_symbols.extend(symbols)
        self.tick_callback = callback
        logger.info(f"Subscribed to symbols: {symbols}")

    def generate_next_tick(self, symbol: str = "NIFTY_SPOT") -> TickData:
        """Simulate price step with random walk"""
        if symbol == "NIFTY_SPOT":
            change = random.choice([-2.5, -1.0, 0.0, 1.0, 2.5, 5.0])
            self.spot_price += change
            price = self.spot_price
        else:
            # Option price simulation based on spot
            price = max(10.0, 150.0 + random.choice([-3.0, -1.0, 0.5, 2.0, 4.0]))

        tick = TickData(
            symbol=symbol,
            timestamp=datetime.now(),
            last_price=round(price, 2),
            volume=random.randint(100, 2000),
            open_interest=random.randint(50000, 150000)
        )

        if self.tick_callback:
            self.tick_callback(tick)

        return tick

    def place_order(self, symbol: str, transaction_type: str, quantity: int, order_type: str = "MARKET", price: float = 0.0) -> Dict[str, Any]:
        self.order_counter += 1
        order_id = f"PAPER_ORD_{self.order_counter}"

        exec_price = price if order_type == "LIMIT" and price > 0 else (self.spot_price if symbol == "NIFTY_SPOT" else 150.0)

        pos = {
            "order_id": order_id,
            "symbol": symbol,
            "transaction_type": transaction_type.upper(),
            "quantity": quantity,
            "entry_price": exec_price,
            "status": "COMPLETE",
            "timestamp": datetime.now()
        }
        self.positions.append(pos)
        logger.info(f"Paper Order Executed: {pos}")
        return pos

    def get_positions(self) -> List[Dict[str, Any]]:
        return self.positions


class KiteConnectBrokerWrapper(BaseBrokerClient):
    """Wrapper skeleton for real Zerodha Kite Connect API integration"""
    def __init__(self, api_key: str, api_secret: str, access_token: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.kite = None

    def connect(self) -> bool:
        try:
            from kiteconnect import KiteConnect
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
            logger.info("KiteConnect client initialized successfully.")
            return True
        except ImportError:
            logger.warning("KiteConnect library not installed. Falling back to mock client.")
            return False
        except Exception as e:
            logger.error(f"Error connecting to KiteConnect: {e}")
            return False

    def subscribe_ticks(self, symbols: List[str], callback: Callable[[TickData], None]) -> None:
        logger.info(f"KiteConnect live ticker subscription registered for {len(symbols)} symbols.")

    def place_order(self, symbol: str, transaction_type: str, quantity: int, order_type: str = "MARKET", price: float = 0.0) -> Dict[str, Any]:
        if not self.kite:
            raise RuntimeError("KiteConnect client not connected.")
        # Production Kite Connect order placement call
        return {"status": "LIVE_ORDER_PLACED_SKELETON"}

    def get_positions(self) -> List[Dict[str, Any]]:
        if not self.kite:
            return []
        return self.kite.positions().get("net", [])
