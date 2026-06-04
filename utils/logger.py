import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union

def setup_logger(name: str = 'nifty_bot', log_file: Optional[Union[str, Path]] = None, level: int = logging.INFO) -> logging.Logger:
    """Function to setup as many loggers as you want"""

    project_root = Path(__file__).parent.parent
    if log_file is None:
        resolved_log_file = project_root / 'logs' / 'nifty_bot.log'
    else:
        resolved_log_file = Path(log_file)

    # Ensure logs directory exists
    log_dir = resolved_log_file.parent
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Rotating File Handler
    file_handler = RotatingFileHandler(resolved_log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger

# Default logger instance
logger: logging.Logger = setup_logger()
