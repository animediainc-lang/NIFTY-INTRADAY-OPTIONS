from data.breeze_client import breeze_client
from data.pre_market_analyzer import pre_market_analyzer
from app_config.config_loader import config
from logger import logger
import sys

def main():
    """Main entry point for the trading bot."""
    try:
        # Step 1: Load Configuration
        config.load_config("app_config/config.yaml")
        logger.info("Configuration loaded successfully.")

        # Step 2: Initialize Broker Session
        # Crucial: Must have a session before making API calls
        if breeze_client.generate_session():
            logger.info("Broker session established.")
        else:
            logger.warning("Starting without active broker session. API calls may fail.")

        # Step 3: Pre-Market Analysis
        expiry = config.get("trading.expiry_date", "2023-11-02T00:00:00.000Z")
        pre_market_metrics = pre_market_analyzer.run_full_analysis(expiry)
        logger.info(f"Pre-market metrics: {pre_market_metrics}")

        logger.info("Nifty Trading Bot initialized and ready.")

    except Exception as e:
        logger.critical(f"Failed to start the bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
