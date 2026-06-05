# Nifty Intraday Options Trading Bot (Breeze API)

## Module 1-9: Core Engine & Database
- **Market Data:** WebSocket ticks to 1m, 3m, 5m candles.
- **Strategies:** Momentum, ORB, Trend Continuation with AI filtering.
- **Risk & Execution:** Capital protection, auto-sizing, multi-target exits.
- **Database:** SQLite persistence for trades, signals, and metrics.

## Module 10: Telegram Notifications

### Architecture Explanation
The Telegram module provides real-time alerting to keep the user informed of the bot's status and trading activities.

- **Telegram Notifier (`telegram/telegram_notifier.py`):**
  - **Asynchronous messaging:** Sends alerts via the Telegram Bot API.
  - **Market Open Summary:** Daily notification of pre-market metrics (VIX, PCR, Max Pain).
  - **Trade Lifecycle Alerts:** Real-time messages for entry, target hits (partial booking), and final exits with PnL.
  - **System Health:** Alerts on API connection failures or critical errors.

### Configuration
Add your bot credentials to `.env`:
```env
BOT_TELEGRAM_BOT_TOKEN=your_token
BOT_TELEGRAM_CHAT_ID=your_chat_id
```

### Folder Structure
```
/telegram
  - telegram_notifier.py
```

### Testing Instructions
Verify notification delivery logic (using mocks):
```bash
python3 -m pytest tests/test_telegram.py
```
