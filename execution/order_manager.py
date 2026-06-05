from data.breeze_client import breeze_client
from logger import logger
from typing import Dict, Any, List, Optional

class OrderManager:
    def __init__(self):
        self.active_positions: Dict[str, Dict[str, Any]] = {}

    def place_order(self, stock_code: str, exchange_code: str, action: str,
                    order_type: str, quantity: int, price: float = 0,
                    stop_loss: float = 0, product: str = "options",
                    expiry_date: str = "", strike_price: str = "0",
                    right: str = "others") -> Dict[str, Any]:
        """
        Places an order via Breeze API.
        action: 'buy' or 'sell'
        order_type: 'market', 'limit', 'stoploss'
        """
        try:
            response = breeze_client.breeze.place_order(
                stock_code=stock_code,
                exchange_code=exchange_code,
                product=product,
                action=action,
                order_type=order_type,
                stoploss=str(stop_loss),
                quantity=str(quantity),
                price=str(price),
                validity="day",
                expiry_date=expiry_date,
                right=right,
                strike_price=strike_price
            )

            if response.get("Status") == 200:
                order_id = response.get("Success", {}).get("order_id")
                logger.info(f"Order placed successfully: {action} {quantity} {stock_code} ID: {order_id}")
                return response
            else:
                logger.error(f"Order placement failed: {response.get('Error')}")
                return response

        except Exception as e:
            logger.error(f"Exception while placing order: {e}")
            return {"Status": 500, "Error": str(e)}

    def get_positions(self) -> List[Dict[str, Any]]:
        """Fetches current open positions from the broker."""
        try:
            response = breeze_client.breeze.get_portfolio_positions()
            if response.get("Status") == 200:
                return response.get("Success", [])
            return []
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def emergency_square_off(self):
        """Closes all open positions immediately."""
        positions = self.get_positions()
        for pos in positions:
            qty = int(pos.get("quantity", 0))
            if qty != 0:
                action = "sell" if qty > 0 else "buy"
                self.place_order(
                    stock_code=pos["stock_code"],
                    exchange_code=pos["exchange_code"],
                    action=action,
                    order_type="market",
                    quantity=abs(qty),
                    product=pos["product_type"],
                    expiry_date=pos.get("expiry_date", ""),
                    strike_price=pos.get("strike_price", "0"),
                    right=pos.get("right", "others")
                )
                logger.warning(f"Emergency square-off: {pos['stock_code']} {qty}")

# Global Order Manager
order_manager = OrderManager()
