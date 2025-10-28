"""
Logging configuration for the Google Tasks CLI application.
"""

import logging
import os
from pathlib import Path


def setup_logger(name='gtasks'):
    """
    Configure application logging with:
    - Console output (INFO level)
    - File output with rotation (DEBUG level)
    - Structured log format
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Configured logger instance
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Log directory
    log_dir = Path.home() / '.gtasks' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Console handler (INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    
    # File handler with rotation (DEBUG)
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_dir / 'gtasks.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console)
    logger.addHandler(file_handler)
    
    return logger