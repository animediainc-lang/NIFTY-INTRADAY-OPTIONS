import pandas as pd
from typing import List, Dict, Any
from strategies.base_strategy import BaseStrategy
from risk.position_sizer import position_sizer
from logger import logger

class BacktestEngine:
    def __init__(self, initial_capital: float = 200000.0):
        self.capital = initial_capital
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve = [initial_capital]

    def run(self, strategy: BaseStrategy, data: pd.DataFrame, sl_points: float = 30, tp_points: float = 60):
        """
        Simulates a backtest over provided OHLC data.
        """
        logger.info(f"Starting backtest for {strategy.name} with {self.capital} capital.")

        in_position = False
        entry_price = 0
        quantity = 0

        for i in range(50, len(data)):
            window = data.iloc[:i+1]
            strategy.update_data(window)

            current_row = data.iloc[i]
            price = current_row['close']

            if not in_position:
                if strategy.check_entry():
                    # Calculate position size
                    risk_amt = self.capital * 0.01 # 1% risk
                    quantity = position_sizer.calculate_quantity(risk_amt, price, price - sl_points, is_option=True)

                    if quantity > 0:
                        entry_price = price
                        in_position = True
                        logger.info(f"Backtest Entry: {current_row.name} at {entry_price}")
            else:
                # 1. Check Stop Loss
                if price <= (entry_price - sl_points):
                    pnl = -sl_points * quantity * 0.5 # Option delta proxy
                    self._record_trade(current_row.name, "SELL_SL", entry_price, price, quantity, pnl)
                    in_position = False

                # 2. Check Take Profit
                elif price >= (entry_price + tp_points):
                    pnl = tp_points * quantity * 0.5
                    self._record_trade(current_row.name, "SELL_TP", entry_price, price, quantity, pnl)
                    in_position = False

                # 3. Check Strategy Exit
                elif strategy.check_exit():
                    pnl = (price - entry_price) * quantity * 0.5
                    self._record_trade(current_row.name, "SELL_SIGNAL", entry_price, price, quantity, pnl)
                    in_position = False

    def _record_trade(self, timestamp, exit_type, entry, exit, qty, pnl):
        self.capital += pnl
        self.equity_curve.append(self.capital)
        self.trades.append({
            "exit_time": timestamp,
            "exit_type": exit_type,
            "entry_price": entry,
            "exit_price": exit,
            "quantity": qty,
            "pnl": round(pnl, 2),
            "balance": round(self.capital, 2)
        })
        logger.info(f"Backtest Trade: {exit_type} PnL: {pnl:.2f} Balance: {self.capital:.2f}")

    def get_results(self) -> pd.DataFrame:
        return pd.DataFrame(self.trades)
