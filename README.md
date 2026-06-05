# Nifty Intraday Options Trading Bot (Breeze API)

## Module 1: Project Foundation
- **Configuration:** Singleton `app_config/config_loader.py`.
- **Logging:** Centralized `logger.py`.

## Module 2: Market Data Layer
- **WebSocket:** Real-time ticks with reconnection.
- **Candles:** Incremental OHLCV+OI generation.

## Module 3: Pre-Market Analysis Layer
- **Analyzer:** PDH/PDL, PCR, Max Pain calculations.

## Module 4: Strategy Engine
- **Strategies:** Momentum Breakout, Trend Continuation, ORB.
- **Wiring:** Automated signal detection on candle close.

## Module 5: Risk Management
- **Risk Manager:** Daily drawdown and trade count enforcement.

## Module 6: Position Sizing
- **Sizer:** Automated lot-size calculation based on risk amount and SL points.

## Module 7: Execution Engine

### Architecture Explanation
The Execution Engine is responsible for the final stage of the trade lifecycle: placing orders and managing open trades.

- **Order Manager (`execution/order_manager.py`):**
  - Interfaces with the Breeze API to place Market, Limit, and Stop-Loss orders.
  - Tracks open portfolio positions.
  - **Emergency Square Off:** A fail-safe to close all active positions immediately.
- **Trade Executor (`execution/trade_executor.py`):**
  - **Signal Coordination:** Orchestrates the flow from Strategy Signal -> Risk Check -> Position Sizing -> Order Placement.
  - **Trade Lifecycle Management:** Monitros active trades for Target 1 (Partial Profits), Target 2 (Full Exit), and Stop-Loss hits.
  - **Trailing Stop Loss (TSL):** Automatically moves SL to cost once Target 1 is achieved.

### Folder Structure
```
/execution
  - order_manager.py
  - trade_executor.py
```

### Testing Instructions
Verify order flow and trade management logic:
```bash
python3 -m pytest tests/test_execution.py
```
