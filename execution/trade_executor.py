from execution.order_manager import order_manager
from risk.risk_manager import risk_manager
from risk.position_sizer import position_sizer
from logger import logger
from typing import Dict, Any, Optional

class TradeExecutor:
    def __init__(self):
        # Key: symbol + strategy_name
        self.active_trades: Dict[str, Dict[str, Any]] = {}

    def execute_signal(self, signal: str, strategy_name: str, symbol: str,
                       current_price: float, stop_loss: float,
                       expiry_date: str = "", strike_price: str = "0",
                       right: str = "others", exchange: str = "NFO"):
        """Process a BUY/SELL signal and manage execution."""
        trade_key = f"{symbol}_{strategy_name}"

        if signal == "BUY":
            self._handle_buy(trade_key, strategy_name, symbol, current_price, stop_loss, expiry_date, strike_price, right, exchange)
        elif signal == "SELL":
            self._handle_sell(trade_key, exit_price=current_price)

    def _handle_buy(self, trade_key, strategy_name, symbol, entry_price, stop_loss, expiry, strike, right, exchange):
        if not risk_manager.check_execution_risk():
            return

        risk_amt = risk_manager.get_max_risk_amount()
        # Indicate this is an option trade for correct sizing (applying delta factor)
        quantity = position_sizer.calculate_quantity(risk_amt, entry_price, stop_loss, is_option=True)

        if quantity <= 0:
            return

        response = order_manager.place_order(
            stock_code=symbol,
            exchange_code=exchange,
            action="buy",
            order_type="market",
            quantity=quantity,
            expiry_date=expiry,
            strike_price=strike,
            right=right
        )

        if response.get("Status") == 200:
            order_id = response["Success"]["order_id"]
            self.active_trades[trade_key] = {
                "symbol": symbol,
                "strategy": strategy_name,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "quantity": quantity,
                "order_id": order_id,
                "expiry_date": expiry,
                "strike_price": strike,
                "right": right,
                "exchange": exchange,
                "target_1": entry_price + (entry_price - stop_loss) * 1.5,
                "target_2": entry_price + (entry_price - stop_loss) * 3.0,
                "partial_booked": False
            }
            logger.info(f"TRADE OPENED: {trade_key} at {entry_price}")

    def _handle_sell(self, trade_key, exit_price: Optional[float] = None):
        """Standard exit signal handler."""
        if trade_key in self.active_trades:
            trade = self.active_trades[trade_key]
            order_manager.place_order(
                stock_code=trade["symbol"],
                exchange_code=trade["exchange"],
                action="sell",
                order_type="market",
                quantity=trade["quantity"],
                expiry_date=trade["expiry_date"],
                strike_price=trade["strike_price"],
                right=trade["right"]
            )

            if exit_price:
                # IMPORTANT: PnL from Spot-referenced trades must be scaled by Delta (0.5)
                # because 1 point in spot is approx 0.5 in option premium.
                pnl = (exit_price - trade["entry_price"]) * trade["quantity"] * 0.5
                risk_manager.update_pnl(pnl)

            del self.active_trades[trade_key]
            logger.info(f"TRADE CLOSED: {trade_key}")

    def manage_active_trades(self, current_prices: Dict[str, float]):
        """Manages Targets, TSL, and Partial Profits."""
        for trade_key, trade in list(self.active_trades.items()):
            symbol = trade["symbol"]
            price = current_prices.get(symbol)
            if not price:
                continue

            # 1. Check Stop Loss
            if price <= trade["stop_loss"]:
                logger.warning(f"STOP LOSS HIT for {trade_key}")
                self._handle_sell(trade_key, exit_price=price)
                continue

            # 2. Check Target 1 (Partial Booking 50%)
            if not trade["partial_booked"] and price >= trade["target_1"]:
                book_qty = trade["quantity"] // 2
                if book_qty > 0:
                    order_manager.place_order(
                        stock_code=symbol,
                        exchange_code=trade["exchange"],
                        action="sell",
                        order_type="market",
                        quantity=book_qty,
                        expiry_date=trade["expiry_date"],
                        strike_price=trade["strike_price"],
                        right=trade["right"]
                    )
                    trade["quantity"] -= book_qty
                    trade["partial_booked"] = True
                    trade["stop_loss"] = trade["entry_price"]
                    logger.info(f"TARGET 1 HIT for {trade_key}: Booked 50%, SL to cost.")

            # 3. Check Target 2 (Full Exit)
            if price >= trade["target_2"]:
                logger.info(f"TARGET 2 HIT for {trade_key}: Full exit.")
                self._handle_sell(trade_key, exit_price=price)

# Global Trade Executor
trade_executor = TradeExecutor()
