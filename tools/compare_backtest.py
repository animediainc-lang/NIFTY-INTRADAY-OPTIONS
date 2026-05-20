import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

def run_comparison_backtest(initial_capital=100000):
    print("Fetching historical data for NIFTY 50...")
    # Get 1 year of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    nifty = yf.download("^NSEI", start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

    if nifty.empty:
        print("Failed to fetch data.")
        return

    lot_size = 50

    def simulate(strategy_name, margin_per_lot, sl_per_lot, target_per_lot, theta_mult, gamma_mult):
        capital = initial_capital
        results = []
        for date, row in nifty.iterrows():
            # Handle both MultiIndex and SingleIndex
            try:
                open_val = row['Open'].iloc[0] if isinstance(row['Open'], pd.Series) else row['Open']
                close_val = row['Close'].iloc[0] if isinstance(row['Close'], pd.Series) else row['Close']
            except:
                open_val = row['Open']
                close_val = row['Close']

            if pd.isna(open_val) or pd.isna(close_val): continue

            spot_open, spot_close = float(open_val), float(close_val)
            lots = int(capital / margin_per_lot)
            if lots < 1: break

            move_pct = abs(spot_close - spot_open) / spot_open
            premium_sold = spot_open * theta_mult
            profit_from_decay = premium_sold * 0.15 # 15% decay intraday
            loss_from_move = premium_sold * (move_pct * gamma_mult)

            daily_pnl = (profit_from_decay - loss_from_move) * lot_size
            daily_pnl = max(-sl_per_lot, min(target_per_lot, daily_pnl))

            total_pnl = daily_pnl * lots
            capital += total_pnl
            results.append({'Date': date, 'PnL': total_pnl, 'Cap': capital})

        df = pd.DataFrame(results)
        if df.empty: return {
            'Strategy': strategy_name,
            'Final Cap': initial_capital,
            'Return %': 0.0,
            'Win Rate %': 0.0,
            'Max DD %': 0.0
        }

        final_return = ((capital - initial_capital) / initial_capital) * 100
        win_rate = (len(df[df['PnL'] > 0]) / len(df)) * 100
        max_dd = ((df['Cap'].cummax() - df['Cap']) / df['Cap'].cummax()).max() * 100

        return {
            'Strategy': strategy_name,
            'Final Cap': round(capital, 2),
            'Return %': round(final_return, 2),
            'Win Rate %': round(win_rate, 2),
            'Max DD %': round(max_dd, 2)
        }

    # ATM Straddle Settings (Unhedged, higher risk)
    straddle_res = simulate("ATM Straddle", 50000, 2000, 1500, 0.012, 45)
    # Iron Condor Settings (Hedged, lower risk, lower margin)
    condor_res = simulate("Iron Condor", 30000, 1000, 800, 0.008, 20)

    # Display in tabular form
    df_compare = pd.DataFrame([straddle_res, condor_res])

    print("\n" + "="*70)
    print("STRATEGY PERFORMANCE COMPARISON (1 YEAR)")
    print("="*70)
    print(df_compare.to_string(index=False))
    print("="*70)
    print("\n* Iron Condor results assume aggressive compounding.")
    print("* Calculations include Stop-Loss and Target profit rules per lot.")

if __name__ == "__main__":
    run_comparison_backtest()
