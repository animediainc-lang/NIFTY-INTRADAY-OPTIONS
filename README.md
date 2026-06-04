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
- **Base Class:** Abstract foundation for strategies.
- **Strategies:** Momentum Breakout, Trend Continuation, ORB.
- **Wiring:** Automated signal detection on candle close.

## Module 5: Risk Management

### Architecture Explanation
The Risk Management module serves as a safety firewall, ensuring the bot adheres to capital protection rules.

- **Risk Manager (`risk/risk_manager.py`):**
  - **Capital Protection:** Enforces maximum 1% risk per trade and 3% daily drawdown.
  - **Trade Limits:** Restricts the bot to a maximum of 5 trades per day.
  - **Time-Based Exit:** Prevents new trades after 15:15 and prepares for session square-off.
  - **Volatility Filter:** Optionally blocks trades during extreme market volatility (India VIX filter).
  - **Auto-Shutdown:** Automatically disables signal processing if daily loss limits are hit.

### Folder Structure
```
/risk
  - risk_manager.py
```

### Testing Instructions
Verify risk logic and limit enforcement:
```bash
python3 -m pytest tests/test_risk.py
```
