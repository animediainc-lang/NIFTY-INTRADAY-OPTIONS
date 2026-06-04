import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "trading_bot", log_file: str = "logs/bot.log", level: int = logging.INFO) -> logging.Logger:
    """Sets up a logger with console and rotating file handlers."""

    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if they already exist (to prevent duplicate logs)
    if not logger.handlers:
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Rotating file handler (10MB per file, max 5 backups)
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Default logger instance
logger = setup_logger()
