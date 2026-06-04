# Module 1: Infrastructure

## Architecture Explanation
The infrastructure layer provides the foundational services for the Nifty Intraday Options Trading Bot. It follows a modular design with clear separation of concerns:

- **Core Configuration (`core/config_loader.py`)**: Implements a thread-safe Singleton `Config` class. It uses `PyYAML` to load settings from `config/config.yml`. It supports nested key access (e.g., `get("strategy.timeframe")`) and uses absolute path resolution relative to the project root for robustness across different execution environments.
- **Logging Utility (`utils/logger.py`)**: Provides a centralized logging system. It configures a standard `logging.Logger` with two handlers:
    - `StreamHandler`: For real-time console output.
    - `RotatingFileHandler`: Targets `logs/nifty_bot.log` with a 10MB limit and 5-file rotation to prevent disk exhaustion.
- **Project Structure**: A predefined directory hierarchy is established to organize various system components (strategies, execution, risk management, etc.), ensuring scalability and maintainability.

## Deployment Instructions
1. **Environment Setup**:
   - Ensure Python 3.12+ is installed.
   - Install dependencies: `pip install -r requirements.txt`.
2. **Configuration**:
   - Edit `config/config.yml` and provide your Breeze API credentials and Telegram bot details.
3. **Execution**:
   - Run the bot using `python3 main.py`.

## Security Best Practices
- **Secret Management**: Never commit `config/config.yml` if it contains real API keys. Use the provided `.gitignore` to prevent sensitive files (like `.env` or local logs) from being pushed to version control.
- **YAML Loading**: The system uses `yaml.safe_load()` to mitigate risks associated with untrusted YAML data.
- **Log Security**: Ensure the `logs/` directory has restricted permissions in production to prevent unauthorized access to trading logs which might contain sensitive execution details.
