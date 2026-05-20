import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

def run_comparison_backtest(initial_capital=100000):
    print("Fetching historical data for NIFTY 50...")
    nifty = yf.download("^NSEI", start=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'), end=datetime.now().strftime('%Y-%m-%d'))

    if nifty.empty:
        print("Failed to fetch data.")
        return

    lot_size = 50

    def simulate(strategy_name, margin_per_lot, sl_per_lot, target_per_lot, theta_mult, gamma_mult):
        capital = initial_capital
        results = []
        for date, row in nifty.iterrows():
            open_val = row['Open'].item() if hasattr(row['Open'], 'item') else row['Open']
            close_val = row['Close'].item() if hasattr(row['Close'], 'item') else row['Close']
            if pd.isna(open_val) or pd.isna(close_val): continue

            spot_open, spot_close = float(open_val), float(close_val)
            lots = int(capital / margin_per_lot)
            if lots < 1: break

            move_pct = abs(spot_close - spot_open) / spot_open
            premium_sold = spot_open * theta_mult
            profit_from_decay = premium_sold * 0.15
            loss_from_move = premium_sold * (move_pct * gamma_mult)

            daily_pnl = (profit_from_decay - loss_from_move) * lot_size
            daily_pnl = max(-sl_per_lot, min(target_per_lot, daily_pnl))

            total_pnl = daily_pnl * lots
            capital += total_pnl
            results.append({'Date': date, 'PnL': total_pnl, 'Cap': capital})

        df = pd.DataFrame(results)
        if df.empty: return None
        return {
            'Final Cap': capital,
            'Return': ((capital - initial_capital) / initial_capital) * 100,
            'Win Rate': (len(df[df['PnL'] > 0]) / len(df)) * 100,
            'Max DD': ((df['Cap'].cummax() - df['Cap']) / df['Cap'].cummax()).max() * 100
        }

    # ATM Straddle Settings
    straddle = simulate("ATM Straddle", 50000, 2000, 1500, 0.012, 45)
    # Iron Condor Settings (lower theta, lower gamma risk, lower margin)
    condor = simulate("Iron Condor", 30000, 1000, 800, 0.008, 20)

    print("\nComparison Results:")
    print(f"Straddle: {straddle}")
    print(f"Condor: {condor}")

if __name__ == "__main__":
    run_comparison_backtest()
