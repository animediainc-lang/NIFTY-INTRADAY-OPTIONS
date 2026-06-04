# Nifty Intraday Options Trading Bot (Breeze API)

## Module 1: Project Foundation
- **Configuration Management:** Singleton `app_config/config_loader.py`.
- **Logging System:** Centralized `logger.py` with rotation.
- **Project Structure:** Organized into functional directories.

## Module 2: Market Data Layer
- **Breeze Client:** SDK wrapper for REST APIs and session management.
- **WebSocket Manager:** Real-time tick streaming with reconnection logic.
- **Candle Manager:** Incremental OHLC generation (1m, 3m, 5m).

## Module 3: Pre-Market Analysis Layer

### Architecture Explanation
The Pre-market Analysis Layer calculates critical market context before the trading session starts.

- **Pre-Market Analyzer (`data/pre_market_analyzer.py`):**
  - **Previous Day Analysis:** Fetches historical data to calculate PDH (Previous Day High), PDL (Previous Day Low), and PDC (Previous Day Close).
  - **Option Chain Analysis:** Calculates PCR (Put Call Ratio) and Max Pain to gauge market sentiment and potential reversal zones.
  - **India VIX:** (Planned) Integrated into the analysis to adjust risk parameters.
  - **Sentiment:** A stub for global market sentiment integration.

### Testing Instructions
Run all tests including analysis tests:
```bash
python3 -m pytest tests/test_foundation.py tests/test_market_data.py tests/test_analysis.py
```

### Deployment Instructions
The `main.py` entry point now automatically executes the pre-market analysis sequence upon startup. Ensure your `app_config/config.yaml` or `.env` file contains the relevant expiry date for Nifty options.
