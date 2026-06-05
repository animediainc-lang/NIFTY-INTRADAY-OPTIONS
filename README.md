# Nifty Intraday Options Trading Bot (Breeze API)

## Module 1: Project Foundation
- **Configuration:** Singleton `app_config/config_loader.py`.
- **Logging:** Centralized `logger.py`.

## Module 2: Market Data Layer
- **WebSocket:** Real-time ticks with reconnection.
- **Candles:** Incremental OHLCV+OI generation.

## Module 3: Pre-Market Analysis Layer
- **Analyzer:** PDH/PDL, PCR, Max Pain, and India VIX calculations.

## Module 4: Strategy Engine
- **Strategies:** Momentum Breakout, Trend Continuation, ORB.
- **Wiring:** Automated signal detection on candle close.

## Module 5: Risk Management
- **Risk Manager:** Daily drawdown and trade count enforcement.

## Module 6: Position Sizing
- **Sizer:** Automated lot-size calculation with Option Delta proxy.

## Module 7: Execution Engine
- **Order Manager:** Breeze API interface with emergency square-off.
- **Trade Executor:** End-to-end lifecycle management (SL/TSL/Targets).

## Module 8: AI Decision Filter
- **AI Filter:** Generates quality scores (0-100) to filter trades.

## Module 9: Database Logging

### Architecture Explanation
The Database module provides persistent storage for all system activities, enabling post-trade analysis and performance tracking.

- **Database Manager (`database/db_manager.py`):**
  - **SQLite Integration:** Uses a local SQLite database (`database/trading_bot.db`).
  - **Trade Logging:** Records every entry, exit, and partial profit booking with PnL.
  - **Signal Tracking:** Stores every strategy signal and its corresponding AI quality score.
  - **Metrics Storage:** Saves daily pre-market analysis results (PCR, VIX, Max Pain).

### Folder Structure
```
/database
  - db_manager.py
  - trading_bot.db (Generated at runtime)
```

### Testing Instructions
Verify database operations:
```bash
python3 -m pytest tests/test_database.py
```
