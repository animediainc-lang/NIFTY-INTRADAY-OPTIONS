import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from logger import logger
from app_config.config_loader import ConfigLoader
from execution.cost_model import TransactionCostModel
from database.db_manager import DatabaseManager

class BaseBroker(ABC):
    """Abstract Base Class for Broker execution adapters."""

    @abstractmethod
    def place_order(self, symbol: str, action: str, quantity: int, price: float, sl: float, tp: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def exit_position(self, trade_id: str, exit_price: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        pass

class PaperBroker(BaseBroker):
    """Simulates realistic paper trading with slippage, cost models, and SQLite audit persistence."""

    def __init__(self, initial_balance: float = 500000.0):
        self.balance = initial_balance
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.cost_model = TransactionCostModel()
        self.db = DatabaseManager()

    def place_order(self, symbol: str, action: str, quantity: int, price: float, sl: float, tp: float) -> Dict[str, Any]:
        trade_id = f"PAPER_{uuid.uuid4().hex[:8].upper()}"

        # Calculate execution cost & slippage
        costs = self.cost_model.calculate_costs(action, price, quantity)
        executed_price = price + (self.cost_model.slippage_points if "BUY" in action else -self.cost_model.slippage_points)

        trade_record = {
            "trade_id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "entry_price": executed_price,
            "exit_price": None,
            "stop_loss": sl,
            "take_profit": tp,
            "pnl": 0.0,
            "slippage": costs["slippage_cost"],
            "total_costs": costs["total_cost"],
            "status": "OPEN",
            "strategy": "AI_MULTI_AGENT",
            "mode": "PAPER"
        }

        self.positions[trade_id] = trade_record
        self.db.log_trade(trade_record)

        logger.info(f"[PAPER BROKER] Executed {action} {quantity} lots of {symbol} at {executed_price:.2f} (Costs: ₹{costs['total_cost']})")
        return trade_record

    def exit_position(self, trade_id: str, exit_price: float) -> Dict[str, Any]:
        if trade_id not in self.positions:
            raise KeyError(f"Position {trade_id} not found in Paper Broker.")

        trade = self.positions[trade_id]
        quantity = trade["quantity"]
        entry_price = trade["entry_price"]
        action = trade["action"]

        # Calculate costs for exit leg
        exit_costs = self.cost_model.calculate_costs("EXIT", exit_price, quantity)

        # PnL calculation
        if "BUY" in action:
            gross_pnl = (exit_price - entry_price) * quantity
        else:
            gross_pnl = (entry_price - exit_price) * quantity

        total_costs = trade["total_costs"] + exit_costs["total_cost"]
        net_pnl = round(gross_pnl - total_costs, 2)

        trade["exit_price"] = exit_price
        trade["pnl"] = net_pnl
        trade["total_costs"] = total_costs
        trade["status"] = "CLOSED"

        self.balance += net_pnl
        self.db.log_trade(trade)
        del self.positions[trade_id]

        logger.info(f"[PAPER BROKER] Closed {trade_id} at {exit_price:.2f} | Gross PnL: ₹{gross_pnl:.2f} | Net PnL: ₹{net_pnl:.2f}")
        return trade

    def get_positions(self) -> List[Dict[str, Any]]:
        return list(self.positions.values())

class UnifiedBrokerAdapter:
    """Factory and Unified Interface supporting Paper, ICICI Direct, Upstox, and OpenAlgo."""

    def __init__(self, mode: str = "paper"):
        self.config = ConfigLoader()
        self.mode = mode.lower()

        if self.mode == "paper":
            self.broker = PaperBroker(initial_balance=self.config.get("trading.default_capital", 500000.0))
        else:
            logger.info(f"Initializing adapter for {self.mode}. Defaulting fallback to Paper mode for security.")
            self.broker = PaperBroker()

    def execute_signal(self, signal_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        action = signal_dict.get("action")
        if action == "NO_TRADE":
            return None

        symbol = signal_dict.get("symbol")
        lots = signal_dict.get("recommended_lots", 1)
        quantity = lots * self.config.get("trading.lot_size", 25)
        entry_price = signal_dict.get("entry_target_range", [200.0])[0]
        sl = entry_price - signal_dict.get("stop_loss_points", 30.0)
        tp = entry_price + signal_dict.get("take_profit_points", 60.0)

        return self.broker.place_order(symbol, action, quantity, entry_price, sl, tp)
