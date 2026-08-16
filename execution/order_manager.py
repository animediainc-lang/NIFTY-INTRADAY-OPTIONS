import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from data.broker_client import BaseBrokerClient
from risk.risk_manager import RiskEngine
from execution.costs import IndianTransactionCostEngine

logger = logging.getLogger(__name__)

class PaperOrderManager:
    def __init__(self, broker: BaseBrokerClient, risk_engine: RiskEngine, cost_engine: IndianTransactionCostEngine):
        self.broker = broker
        self.risk_engine = risk_engine
        self.cost_engine = cost_engine
        self.active_positions: Dict[str, Dict[str, Any]] = {} # symbol -> position dict
        self.closed_trades: List[Dict[str, Any]] = []

    def execute_signal(self, signal: Dict[str, Any], symbol: str, current_price: float, timestamp: datetime) -> Optional[Dict[str, Any]]:
        action = signal.get("decision", "NO_TRADE")
        if action not in ["BUY_CALL", "BUY_PUT"]:
            return None

        # Check risk engine validation
        valid, msg = self.risk_engine.validate_new_trade(timestamp)
        if not valid:
            logger.warning(f"Order Execution Rejected: {msg}")
            return None

        llm_decision = signal.get("llm_brain_decision", {})
        sl_points = llm_decision.get("suggested_stop_loss_points", 15.0)
        tp_points = llm_decision.get("suggested_target_points", 30.0)

        quantity = self.risk_engine.calculate_position_size(current_price, sl_points)

        order_res = self.broker.place_order(symbol=symbol, transaction_type="BUY", quantity=quantity, price=current_price)

        position = {
            "order_id": order_res["order_id"],
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "entry_price": current_price,
            "current_price": current_price,
            "stop_loss_price": max(0.1, current_price - sl_points),
            "target_price": current_price + tp_points,
            "entry_time": timestamp,
            "status": "OPEN",
            "trailing_sl_actuated": False
        }

        self.active_positions[symbol] = position
        logger.info(f"Position Opened [{action}]: {position}")
        return position

    def update_positions(self, current_tick_symbol: str, current_price: float, current_time: datetime) -> List[Dict[str, Any]]:
        exited_trades = []
        if current_tick_symbol not in self.active_positions:
            # Check auto square off for all positions
            if self.risk_engine.is_auto_square_off_time(current_time):
                for sym in list(self.active_positions.keys()):
                    pos = self.active_positions[sym]
                    exited = self._exit_position(pos, pos["current_price"], current_time, "AUTO_SQUARE_OFF_1515")
                    exited_trades.append(exited)
            return exited_trades

        pos = self.active_positions[current_tick_symbol]
        pos["current_price"] = current_price

        # Trailing Stop Loss Logic: move SL to breakeven once price covers 50% target
        half_target = pos["entry_price"] + 0.5 * (pos["target_price"] - pos["entry_price"])
        if not pos["trailing_sl_actuated"] and current_price >= half_target:
            pos["stop_loss_price"] = pos["entry_price"]
            pos["trailing_sl_actuated"] = True
            logger.info(f"Trailing SL actuated to breakeven ({pos['entry_price']}) for {pos['symbol']}")

        # Check exit triggers
        exit_reason = None
        if current_price <= pos["stop_loss_price"]:
            exit_reason = "STOP_LOSS_HIT"
        elif current_price >= pos["target_price"]:
            exit_reason = "TARGET_HIT"
        elif self.risk_engine.is_auto_square_off_time(current_time):
            exit_reason = "AUTO_SQUARE_OFF_1515"

        if exit_reason:
            exited = self._exit_position(pos, current_price, current_time, exit_reason)
            exited_trades.append(exited)

        return exited_trades

    def _exit_position(self, pos: Dict[str, Any], exit_price: float, exit_time: datetime, reason: str) -> Dict[str, Any]:
        symbol = pos["symbol"]
        costs = self.cost_engine.calculate_trade_costs(buy_price=pos["entry_price"], sell_price=exit_price, quantity=pos["quantity"])

        trade_summary = {
            "symbol": symbol,
            "action": pos["action"],
            "quantity": pos["quantity"],
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "entry_time": pos["entry_time"],
            "exit_time": exit_time,
            "exit_reason": reason,
            "gross_pnl": costs["gross_pnl"],
            "total_costs": costs["total_taxes_and_charges"],
            "net_pnl": costs["net_pnl"]
        }

        # Update Risk Engine
        self.risk_engine.record_trade_result(costs["net_pnl"])

        self.closed_trades.append(trade_summary)
        del self.active_positions[symbol]
        logger.info(f"Position Exited [{reason}]: {trade_summary}")
        return trade_summary
