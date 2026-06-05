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

### Architecture Explanation
The Position Sizing module calculates the optimal trade quantity to ensure risk consistency across different trade setups.

- **Position Sizer (`risk/position_sizer.py`):**
  - **Dynamic Quantity Calculation:** Determines the number of lots based on the current capital, risk percentage, and the distance between entry and stop-loss.
  - **Lot Size Alignment:** Automatically rounds down quantities to the nearest instrument lot size (e.g., multiples of 25 for Nifty).
  - **Exposure Control:** Enforces a maximum total exposure limit to prevent over-leveraging.
  - **Margin Check:** Provides a utility to verify if available funds are sufficient for the calculated position.

### Testing Instructions
Verify lot size logic:
```bash
python3 -m pytest tests/test_position_sizing.py
```
