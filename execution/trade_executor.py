from execution.order_manager import order_manager
from risk.risk_manager import risk_manager
from risk.position_sizer import position_sizer
from database.db_manager import db_manager
from telegram.telegram_notifier import notifier
from logger import logger
from typing import Dict, Any, Optional

class TradeExecutor:
    def __init__(self):
        self.active_trades: Dict[str, Dict[str, Any]] = {}

    def execute_signal(self, signal: str, strategy_name: str, symbol: str,
                       current_price: float, stop_loss: float,
                       expiry_date: str = "", strike_price: str = "0",
                       right: str = "Spot", exchange: str = "NFO"):
        trade_key = f"{symbol}_{strike_price}_{right}_{strategy_name}"

        if signal == "BUY":
            self._handle_buy(trade_key, strategy_name, symbol, current_price, stop_loss, expiry_date, strike_price, right, exchange)
        elif signal == "SELL":
            self._handle_sell(trade_key, exit_price=current_price)

    def _handle_buy(self, trade_key, strategy_name, symbol, entry_price, stop_loss, expiry, strike, right, exchange):
        if not risk_manager.check_execution_risk():
            return

        risk_amt = risk_manager.get_max_risk_amount()
        is_option = (right != "Spot")
        quantity = position_sizer.calculate_quantity(risk_amt, entry_price, stop_loss, is_option=is_option)

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
            right=right if is_option else "others"
        )

        if response.get("Status") == 200:
            order_id = response["Success"]["order_id"]
            trade_data = {
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
            self.active_trades[trade_key] = trade_data
            logger.info(f"TRADE OPENED: {trade_key}")

            db_manager.log_trade(trade_key, strategy_name, "BUY", entry_price, quantity, status="OPEN")
            notifier.notify_trade_entry(trade_data)

    def _handle_sell(self, trade_key, exit_price: Optional[float] = None):
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
                right=trade["right"] if trade["right"] != "Spot" else "others"
            )

            pnl = 0
            if exit_price:
                delta = 0.5 if trade["right"] != "Spot" else 1.0
                pnl = (exit_price - trade["entry_price"]) * trade["quantity"] * delta
                risk_manager.update_pnl(pnl)
                notifier.notify_trade_exit(trade, exit_price, pnl)

            db_manager.log_trade(trade_key, trade["strategy"], "SELL", exit_price or 0, trade["quantity"], pnl, status="CLOSED")
            del self.active_trades[trade_key]
            logger.info(f"TRADE CLOSED: {trade_key}")

    def manage_active_trades(self, current_prices: Dict[str, float]):
        for trade_key, trade in list(self.active_trades.items()):
            spot_key = f"{trade['symbol']}_0_Spot"
            price = current_prices.get(spot_key)
            if not price:
                continue

            if price <= trade["stop_loss"]:
                logger.warning(f"STOP LOSS HIT for {trade_key}")
                self._handle_sell(trade_key, exit_price=price)
                continue

            if not trade["partial_booked"] and price >= trade["target_1"]:
                book_qty = trade["quantity"] // 2
                if book_qty > 0:
                    order_manager.place_order(
                        stock_code=trade["symbol"],
                        exchange_code=trade["exchange"],
                        action="sell",
                        order_type="market",
                        quantity=book_qty,
                        expiry_date=trade["expiry_date"],
                        strike_price=trade["strike_price"],
                        right=trade["right"] if trade["right"] != "Spot" else "others"
                    )
                    trade["quantity"] -= book_qty
                    trade["partial_booked"] = True
                    trade["stop_loss"] = trade["entry_price"]
                    logger.info(f"TARGET 1 HIT for {trade_key}")
                    db_manager.log_trade(trade_key, trade["strategy"], "PARTIAL_SELL", price, book_qty, status="PARTIAL")
                    notifier.send_message(f"🎯 *Target 1 Hit* for `{trade_key}`. Booked 50% profit. SL moved to cost.")

            if price >= trade["target_2"]:
                logger.info(f"TARGET 2 HIT for {trade_key}")
                self._handle_sell(trade_key, exit_price=price)

# Global Trade Executor
trade_executor = TradeExecutor()
