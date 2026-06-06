import pandas as pd
import numpy as np
from typing import Dict, Any

class BacktestReport:
    @staticmethod
    def generate_summary(trades_df: pd.DataFrame, initial_capital: float) -> Dict[str, Any]:
        if trades_df.empty:
            return {"status": "No trades executed"}

        total_trades = len(trades_df)
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]

        win_rate = (len(wins) / total_trades) * 100
        net_pnl = trades_df['pnl'].sum()
        final_balance = initial_capital + net_pnl
        roi = (net_pnl / initial_capital) * 100

        # Max Drawdown
        balance_series = trades_df['balance']
        peak = balance_series.cummax()
        drawdown = (balance_series - peak) / peak
        max_drawdown = drawdown.min() * 100

        # Sharpe Ratio (Simulated daily returns)
        returns = trades_df['pnl'] / initial_capital
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0

        return {
            "Total Trades": total_trades,
            "Win Rate": f"{win_rate:.2f}%",
            "Net PnL": f"₹{net_pnl:.2f}",
            "ROI": f"{roi:.2f}%",
            "Max Drawdown": f"{max_drawdown:.2f}%",
            "Sharpe Ratio": round(sharpe, 2),
            "Final Balance": f"₹{final_balance:.2f}"
        }

    @staticmethod
    def to_tabular_markdown(summary: Dict[str, Any]) -> str:
        header = "| Metric | Value |\n| :--- | :--- |\n"
        rows = "\n".join([f"| {k} | {v} |" for k, v in summary.items()])
        return header + rows
