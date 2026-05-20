import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

def run_backtest(initial_capital=100000):
    print("Fetching historical data for NIFTY 50...")
    # NIFTY 50 index data from Yahoo Finance
    nifty = yf.download("^NSEI", start=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'), end=datetime.now().strftime('%Y-%m-%d'))

    if nifty.empty:
        print("Failed to fetch data.")
        return

    print(f"Backtesting ATM Straddle strategy for 1 year with ₹{initial_capital:,}")

    # Strategy parameters
    lot_size = 50
    results = []
    capital = initial_capital

    for date, row in nifty.iterrows():
        # Skip if not a trading day or missing data
        open_val = row['Open'].item() if hasattr(row['Open'], 'item') else row['Open']
        close_val = row['Close'].item() if hasattr(row['Close'], 'item') else row['Close']
        high_val = row['High'].item() if hasattr(row['High'], 'item') else row['High']
        low_val = row['Low'].item() if hasattr(row['Low'], 'item') else row['Low']

        if pd.isna(open_val) or pd.isna(close_val):
            continue

        spot_open = float(open_val)
        spot_close = float(close_val)
        spot_high = float(high_val)
        spot_low = float(low_val)

        # 1 lot ATM Straddle margin requirement ~ ₹50,000
        lots = int(capital / 50000)
        if lots < 1:
            print(f"Capital depleted at {date}")
            break

        # Daily simulation logic:
        # sell ATM CE + PE at 9:20 AM (Open price used as proxy)
        # exit at 3:10 PM (Close price used as proxy)

        # Net spot change
        move_pct = abs(spot_close - spot_open) / spot_open

        # Average total premium sold ~ 1.2% of spot
        premium_sold = spot_open * 0.012

        # Decay (Theta) is roughly 15% of premium intraday
        profit_from_decay = premium_sold * 0.15

        # Gamma/Delta loss
        loss_from_move = premium_sold * (move_pct * 45) # Multiplier to simulate convexity

        daily_pnl_per_lot = (profit_from_decay - loss_from_move) * lot_size

        # Apply Stop Loss (Rs 2000 per lot)
        if daily_pnl_per_lot < -2000:
            daily_pnl_per_lot = -2000

        # Apply Target (Rs 1500 per lot)
        if daily_pnl_per_lot > 1500:
            daily_pnl_per_lot = 1500

        total_daily_pnl = daily_pnl_per_lot * lots
        capital += total_daily_pnl

        results.append({
            'Date': date,
            'Spot': round(spot_open, 2),
            'Move%': round(move_pct * 100, 2),
            'Daily PnL': round(total_daily_pnl, 2),
            'Capital': round(capital, 2)
        })

    df_res = pd.DataFrame(results)

    if df_res.empty:
        print("No results to display.")
        return

    # Metrics
    total_days = len(df_res)
    winning_days = len(df_res[df_res['Daily PnL'] > 0])
    losing_days = len(df_res[df_res['Daily PnL'] < 0])
    win_rate = (winning_days / total_days) * 100
    total_return = ((capital - initial_capital) / initial_capital) * 100
    max_drawdown = ((df_res['Capital'].cummax() - df_res['Capital']) / df_res['Capital'].cummax()).max() * 100

    print("\n" + "="*40)
    print("BACKTEST RESULTS (1 YEAR)")
    print("="*40)
    print(f"Initial Capital   : ₹{initial_capital:,}")
    print(f"Final Capital     : ₹{capital:,.2f}")
    print(f"Total Return      : {total_return:.2f}%")
    print(f"Max Drawdown      : {max_drawdown:.2f}%")
    print(f"Win Rate          : {win_rate:.2f}% ({winning_days}W / {losing_days}L)")
    print(f"Total Trading Days: {total_days}")
    print("="*40)

    print("\nMonthly Summary:")
    df_res['Month'] = df_res['Date'].dt.to_period('M')
    monthly = df_res.groupby('Month')['Daily PnL'].sum()
    print(monthly)

if __name__ == "__main__":
    run_backtest()
