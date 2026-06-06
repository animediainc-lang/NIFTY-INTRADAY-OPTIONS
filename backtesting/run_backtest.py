import pandas as pd
import numpy as np
from backtesting.engine import BacktestEngine
from backtesting.report_generator import BacktestReport
from strategies.momentum_breakout import MomentumBreakout
from app_config.config_loader import config
from logger import logger

def generate_synthetic_data(years=1):
    """Generates 1 year of synthetic Nifty-like 1m data for demonstration."""
    periods = 250 * 375 * years # ~250 trading days, 375 minutes per day
    idx = pd.date_range("2023-01-01", periods=periods, freq="1min")

    # Simulate a stochastic process with an upward drift
    returns = np.random.normal(0.0001, 0.002, periods)
    price = 18000 * (1 + returns).cumprod()

    df = pd.DataFrame({
        'open': price,
        'high': price * 1.002,
        'low': price * 0.998,
        'close': price,
        'volume': np.random.randint(1000, 5000, periods),
        'oi': np.random.randint(500000, 1000000, periods)
    }, index=idx)
    return df

def run_1year_backtest():
    # 1. Setup
    config.load_config("app_config/config.yaml")
    engine = BacktestEngine(initial_capital=200000.0)
    strategy = MomentumBreakout()

    # 2. Data
    logger.info("Generating 1 year of synthetic market data...")
    data = generate_synthetic_data(years=1)

    # 3. Run
    engine.run(strategy, data, sl_points=30, tp_points=60)

    # 4. Report
    results = engine.get_results()
    summary = BacktestReport.generate_summary(results, 200000.0)

    print("\n" + "="*40)
    print("NIFTY 1-YEAR BACKTEST RESULTS (2L Capital)")
    print("="*40)
    print(BacktestReport.to_tabular_markdown(summary))
    print("="*40 + "\n")

if __name__ == "__main__":
    run_1year_backtest()
