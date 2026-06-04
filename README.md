# Nifty Intraday Options Trading Bot (Breeze API)

## Module 1: Project Foundation

### Architecture Explanation
The foundation of the trading bot is designed with modularity, scalability, and production readiness in mind.

- **Configuration Management (`app_config/config_loader.py`):** Uses a Singleton pattern to ensure global access to configuration settings. It supports loading from a YAML file (`app_config/config.yaml`) and allows overriding any setting using environment variables (prefixed with `BOT_`). It also automatically loads environment variables from a `.env` file if present.
- **Logging System (`logger.py`):** Provides a centralized logging utility that outputs to both the console and a rotating file (`logs/bot.log`). This ensures that logs don't consume infinite disk space while providing necessary audit trails.
- **Directory Structure:** Organizes the project into functional modules such as strategies, execution, risk management, and dashboard, following industry best practices.

## Module 2: Market Data Layer

### Architecture Explanation
The Market Data Layer is responsible for interfacing with the Breeze API to fetch both real-time and historical data.

- **Breeze Client (`data/breeze_client.py`):** A wrapper around the `breeze-connect` SDK. It handles authentication, session generation, and provides clean methods for fetching quotes, option chains, and historical OHLCV data. It uses lazy initialization to ensure configuration is loaded before the SDK is used.
- **WebSocket Manager (`data/websocket_manager.py`):** Manages the persistent WebSocket connection for real-time tick data. Features include:
  - Exponential backoff for automatic reconnection.
  - Automatic resubscription to instruments after a reconnect.
  - Support for multiple callbacks to process ticks.
- **Candle Manager (`data/candle_manager.py`):** An efficient data processor that buffers raw ticks and updates 1-minute, 3-minute, and 5-minute OHLC candles. It only updates the active candle per tick to minimize CPU overhead.

### Folder Structure
```
/app_config  - Configuration files and loader
/data        - Market data logic and storage
/logs        - Application logs
/database    - SQLite/PostgreSQL database files
/strategies  - Trading strategy implementations
/execution   - Order execution logic
/risk        - Risk management rules
/backtesting - Backtesting engine
/dashboard   - Web dashboard (Dash/Streamlit)
/telegram    - Telegram bot integration
/tests       - Unit and integration tests
main.py      - Application entry point
requirements.txt - Project dependencies
logger.py    - Global logging utility
.gitignore   - Git exclusion rules
```

### Deployment Instructions
1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd nifty-bot
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure the bot:**
   - Create a `.env` file or edit `app_config/config.yaml` with your Breeze API credentials.
   - Example `.env`:
     ```
     BOT_BREEZE_API_KEY=your_key
     BOT_BREEZE_API_SECRET=your_secret
     BOT_BREEZE_SESSION_TOKEN=your_token
     ```
4. **Run the bot:**
   ```bash
   python3 main.py
   ```

### Testing Instructions
Run all tests using pytest:
```bash
python3 -m pytest tests/test_foundation.py tests/test_market_data.py
```

### Security Best Practices
- **API Keys:** Never hardcode API keys in the source code. Use a `.env` file (ensure it's in `.gitignore`) or environment variables.
- **Environment Variables:** Use `python-dotenv` for local development and manage secrets securely in production environments.
- **File Permissions:** Ensure the `logs` and `database` directories have appropriate write permissions but are restricted from unauthorized access.
- **Version Control:** Ensure that sensitive files and build artifacts (like `__pycache__`) are excluded via `.gitignore`.
