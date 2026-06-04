import sys
from core.config_loader import get_config
from utils.logger import logger

def main() -> None:
    try:
        # Load Configuration
        config = get_config()
        logger.info("Configuration loaded successfully.")

        # Log basic info
        nifty_symbol = config.get("strategy.nifty_spot_symbol")
        logger.info(f"Starting Nifty Intraday Options Bot for symbol: {nifty_symbol}")

        # Placeholder for further initialization
        logger.info("System initialized. Ready for module implementation.")

    except Exception as e:
        logger.error(f"Failed to start the system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
