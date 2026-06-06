# Nifty Intraday Options Trading Bot (Breeze API)

## System Architecture (Modules 1-12)
- **Market Data:** WebSocket ticks to candles (1m, 3m, 5m).
- **Strategies:** Momentum, ORB, Trend Continuation with AI filtering.
- **Risk & Execution:** Capital protection (1%), auto-sizing, multi-target exits (Target 1 & 2), TSL.
- **Dashboard:** Live web interface (Plotly Dash) with Paper/Live mode indicator.
- **Database:** SQLite persistence for trades, signals, and metrics.
- **Notifications:** Real-time Telegram alerts.
- **Backtesting:** High-fidelity simulation engine for strategy validation.

## Backtesting Engine

### Architecture Explanation
The Backtesting module allows for rigorous validation of strategies using historical data before live deployment.

- **Backtest Engine (`backtesting/engine.py`):**
  - Simulates the entire trading loop, including signal generation, risk validation, and order execution.
  - Supports configurable Stop-Loss and Take-Profit points.
  - Accounts for option delta proxies to estimate realistic PnL for Nifty options.
- **Report Generator (`backtesting/report_generator.py`):**
  - Calculates ROI, Win Rate, Max Drawdown, Sharpe Ratio, and Expectancy.
  - Formats results into professional tabular reports.

### Running a Backtest
To execute a backtest simulation:
```bash
python3 backtesting/run_backtest.py
```

### Folder Structure
```
/backtesting
  - engine.py
  - report_generator.py
  - run_backtest.py
```

### Backtest Verification
Verify the engine logic with unit tests:
```bash
python3 -m pytest tests/test_backtesting.py
```
