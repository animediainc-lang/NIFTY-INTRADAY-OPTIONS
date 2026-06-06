# Nifty Intraday Options Trading Bot (Breeze API)

## Core Modules (1-11)
- **Market Data:** WebSocket ticks to candles (1m, 3m, 5m).
- **Strategies:** Momentum, ORB, Trend Continuation with AI filtering.
- **Risk & Execution:** Capital protection, auto-sizing, multi-target exits.
- **Dashboard:** Live web interface (Plotly Dash).
- **Notifications:** Real-time Telegram alerts.

## Paper Trading vs. Live Mode

The bot supports two execution modes, configurable via `app_config/config.yaml`:

### 1. Paper Trading (Default)
- **Setting:** `trading.mode: "paper"`
- **Behavior:** Bypasses the Breeze API for order placement. Simulates successful entries and exits with a `PAPER_` prefix in the Order ID.
- **Purpose:** Test strategies and system wiring without financial risk.

### 2. Live Trading
- **Setting:** `trading.mode: "live"`
- **Behavior:** Executes real trades via the ICICI Direct Breeze API.
- **Warning:** A critical warning is logged at startup. Ensure all risk parameters are verified before enabling.

### Dashboard Indicator
The dashboard header displays a prominent status tag:
- **YELLOW:** Paper Trading Mode.
- **RED:** Live Trading Mode.

## Testing Instructions
Verify mode switching logic:
```bash
python3 -m pytest tests/test_paper_trading.py
```
