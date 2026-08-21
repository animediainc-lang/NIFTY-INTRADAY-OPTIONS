import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
from execution.cost_model import TransactionCostModel
from logger import logger

class BacktestEngine:
    """Vectorized and Event-driven Backtest Engine with realistic NSE slippage and brokerage modeling."""

    def __init__(self, initial_capital: float = 500000.0):
        self.initial_capital = initial_capital
        self.cost_model = TransactionCostModel()

    def run_backtest(self, df_candles: pd.DataFrame, strategy_name: str = "Directional Momentum Buyer") -> Dict[str, Any]:
        """Runs backtest over historical candle series and outputs detailed equity metrics."""
        capital = self.initial_capital
        equity_curve = [capital]
        trades = []
        in_position = False
        position_type = None
        entry_price = 0.0
        entry_time = None
        quantity = 50 # 2 lots

        for i in range(20, len(df_candles)):
            window = df_candles.iloc[:i]
            latest = window.iloc[-1]
            close = latest["close"]
            timestamp = latest["timestamp"] if "timestamp" in latest else datetime.now().isoformat()

            # Simple SMA crossover for backtest simulation
            sma_fast = window["close"].tail(5).mean()
            sma_slow = window["close"].tail(20).mean()

            if not in_position:
                if sma_fast > sma_slow:
                    in_position = True
                    position_type = "BUY_CE"
                    entry_price = close
                    entry_time = timestamp
                elif sma_fast < sma_slow:
                    in_position = True
                    position_type = "BUY_PE"
                    entry_price = close
                    entry_time = timestamp
            else:
                # Exit conditions (30 pt SL or 60 pt TP)
                price_change = close - entry_price if position_type == "BUY_CE" else entry_price - close
                if price_change >= 60.0 or price_change <= -30.0 or i == len(df_candles) - 1:
                    # Calculate realistic costs
                    entry_costs = self.cost_model.calculate_costs(position_type, entry_price, quantity)
                    exit_costs = self.cost_model.calculate_costs("EXIT", close, quantity)
                    total_costs = entry_costs["total_cost"] + exit_costs["total_cost"]

                    gross_pnl = price_change * quantity
                    net_pnl = gross_pnl - total_costs
                    capital += net_pnl

                    trades.append({
                        "entry_time": entry_time,
                        "exit_time": timestamp,
                        "type": position_type,
                        "entry_price": entry_price,
                        "exit_price": close,
                        "gross_pnl": round(gross_pnl, 2),
                        "total_costs": round(total_costs, 2),
                        "net_pnl": round(net_pnl, 2),
                        "capital_after": round(capital, 2)
                    })

                    in_position = False
                    position_type = None

            equity_curve.append(capital)

        # Performance summary metrics
        df_trades = pd.DataFrame(trades)
        total_trades = len(df_trades)
        if total_trades > 0:
            winning_trades = len(df_trades[df_trades["net_pnl"] > 0])
            losing_trades = len(df_trades[df_trades["net_pnl"] <= 0])
            win_rate = round((winning_trades / total_trades) * 100.0, 2)
            total_net_pnl = round(df_trades["net_pnl"].sum(), 2)
            max_pnl = df_trades["net_pnl"].max()
            min_pnl = df_trades["net_pnl"].min()
        else:
            winning_trades = losing_trades = win_rate = total_net_pnl = max_pnl = min_pnl = 0

        total_return_pct = round(((capital - self.initial_capital) / self.initial_capital) * 100.0, 2)

        return {
            "strategy": strategy_name,
            "initial_capital": self.initial_capital,
            "ending_capital": round(capital, 2),
            "total_return_pct": total_return_pct,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate_pct": win_rate,
            "total_net_pnl": total_net_pnl,
            "max_winning_trade": max_pnl,
            "max_losing_trade": min_pnl,
            "trades": trades,
            "equity_curve": equity_curve
        }
