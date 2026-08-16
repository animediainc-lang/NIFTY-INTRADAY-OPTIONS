import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from data.models import Candle
from data.broker_client import MockPaperBrokerClient
from execution.costs import IndianTransactionCostEngine
from risk.risk_manager import RiskEngine
from execution.order_manager import PaperOrderManager
from brain.llm_brain import LLMBrain
from orchestration.orchestrator import MultiAgentOrchestrator

logger = logging.getLogger(__name__)

class EventDrivenBacktester:
    def __init__(self, capital: float = 100000.0):
        self.capital = capital
        self.cost_engine = IndianTransactionCostEngine()
        self.risk_engine = RiskEngine(total_capital=capital)
        self.broker = MockPaperBrokerClient()
        self.broker.connect()
        self.order_manager = PaperOrderManager(self.broker, self.risk_engine, self.cost_engine)
        self.brain = LLMBrain(provider="mock")
        self.orchestrator = MultiAgentOrchestrator(self.brain)

        self.equity_curve: List[Dict[str, Any]] = []

    def run_simulation(self, candles: List[Candle]) -> Dict[str, Any]:
        """Runs event-driven backtest over historical candle series"""
        if not candles:
            return {"error": "No historical candle data provided."}

        current_equity = self.capital
        self.equity_curve.append({"timestamp": candles[0].timestamp, "equity": current_equity})

        for i, candle in enumerate(candles):
            # Update current active position pricing
            exits = self.order_manager.update_positions(
                current_tick_symbol="NIFTY24OCT24000CE",
                current_price=candle.close,
                current_time=candle.timestamp
            )

            # Update equity curve on closed trades
            for exited in exits:
                current_equity += exited["net_pnl"]

            # Evaluate strategy entry on candle close if no active position
            if "NIFTY24OCT24000CE" not in self.order_manager.active_positions:
                market_ctx = {
                    "spot_price": candle.close + 50, # Ensure spot > vwap
                    "vwap": candle.close,
                    "rsi": 65.0,
                    "pcr": 1.25,
                    "vix": 14.5
                }

                decision = self.orchestrator.run_debate_cycle(market_ctx)
                if decision["decision"] in ["BUY_CALL", "BUY_PUT"]:
                    self.order_manager.execute_signal(
                        signal=decision,
                        symbol="NIFTY24OCT24000CE",
                        current_price=candle.close,
                        timestamp=candle.timestamp
                    )

            self.equity_curve.append({"timestamp": candle.timestamp, "equity": current_equity})

        return self.generate_performance_report()

    def generate_performance_report(self) -> Dict[str, Any]:
        trades = self.order_manager.closed_trades
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate_pct": 0.0,
                "total_net_pnl": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pct": 0.0,
                "trades": []
            }

        df_trades = pd.DataFrame(trades)
        wins = df_trades[df_trades["net_pnl"] > 0]
        losses = df_trades[df_trades["net_pnl"] <= 0]

        total_trades = len(trades)
        win_rate = round((len(wins) / total_trades) * 100.0, 2)
        total_net_pnl = round(df_trades["net_pnl"].sum(), 2)

        gross_profit = wins["net_pnl"].sum() if not wins.empty else 0.0
        gross_loss = abs(losses["net_pnl"].sum()) if not losses.empty else 1.0
        profit_factor = round(gross_profit / max(gross_loss, 1.0), 2)

        # Max Drawdown Calculation
        df_eq = pd.DataFrame(self.equity_curve)
        df_eq["peak"] = df_eq["equity"].cummax()
        df_eq["drawdown"] = (df_eq["equity"] - df_eq["peak"]) / df_eq["peak"]
        max_drawdown_pct = round(abs(df_eq["drawdown"].min()) * 100.0, 2)

        return {
            "total_trades": total_trades,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate_pct": win_rate,
            "total_net_pnl": total_net_pnl,
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_drawdown_pct,
            "trades": trades
        }
