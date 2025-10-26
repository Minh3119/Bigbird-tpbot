import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(name: str = 'discord_bot', log_dir: str = 'logs') -> logging.Logger:
    """Setup and return a logger with both file and console handlers"""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # Changed to INFO to see more logs

    # Create logs directory if it doesn't exist
    Path(log_dir).mkdir(exist_ok=True)

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # File handler (rotating, max 5MB per file, keep 5 backup files)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'discord.log'),
        maxBytes=5_000_000,
        backupCount=5
    )
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(file_formatter)

    # Console handler - keep INFO for startup/shutdown messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger