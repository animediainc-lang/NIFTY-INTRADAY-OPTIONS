from data.breeze_client import breeze_client
from app_config.config_loader import config
from logger import logger
import sys

def main():
    """Main entry point for the trading bot."""
    try:
        # Step 1: Load Configuration
        config.load_config("app_config/config.yaml")
        logger.info("Configuration loaded successfully.")

        # Step 2: Initialize Broker Session (Optional at startup)
        # Success = breeze_client.generate_session()

        logger.info("Nifty Trading Bot initialized.")

        # Keep running
        # ... logic for starting WebSocket, Strategy Engine, etc.

    except Exception as e:
        logger.critical(f"Failed to start the bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
