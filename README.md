# Nifty Intraday Options Trading Bot (Breeze API)

## Module 1: Project Foundation
- **Configuration Management:** Singleton `app_config/config_loader.py`.
- **Logging System:** Centralized `logger.py` with rotation.

## Module 2: Market Data Layer
- **WebSocket Manager:** Real-time tick streaming with reconnection logic.
- **Candle Manager:** Optimized incremental OHLC generation (1m, 3m, 5m).

## Module 3: Pre-Market Analysis Layer
- **Pre-Market Analyzer:** Logic for PDH/PDL, PCR, and Max Pain.

## Module 4: Strategy Engine

### Architecture Explanation
The Strategy Engine implements the core trading logic, designed to be modular and extensible.

- **Base Strategy (`strategies/base_strategy.py`):** An abstract base class that defines the interface for all strategies, ensuring consistency in entry/exit checks and data handling.
- **Indicators (`strategies/indicators.py`):** A collection of optimized technical indicator functions (VWAP, EMA, HHHL) used by the strategies.
- **Implemented Strategies:**
  - **Momentum Breakout (Strategy A):** Focuses on price breakout above VWAP with volume and OI confirmation.
  - **Trend Continuation (Strategy B):** Captures pullbacks to the EMA zone within an established trend.
  - **Opening Range Breakout (Strategy C):** Trades the break of the initial 15-minute range with volume support.

### Testing Instructions
Verify strategy signals with mock data:
```bash
python3 -m pytest tests/test_strategies.py
```

### Folder Structure
```
/strategies
  - base_strategy.py
  - indicators.py
  - momentum_breakout.py
  - trend_continuation.py
  - opening_range_breakout.py
```
