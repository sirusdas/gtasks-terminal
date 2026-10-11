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


def get_log_file_path() -> Path:
    """Return the absolute path to the main log file."""
    return Path.home() / '.gtasks' / 'logs' / 'gtasks.log'


def set_global_log_level(level_name: str) -> str:
    """
    Dynamically update log level across all gtasks loggers.
    Accepts 'DEBUG', 'INFO', 'WARNING', 'ERROR'.
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,
        'ERROR': logging.ERROR
    }
    target_level = level_map.get(level_name.upper(), logging.INFO)
    
    # Update root and all gtasks loggers
    for name in list(logging.root.manager.loggerDict.keys()) + ['gtasks']:
        if 'gtasks' in name or name == 'root':
            l = logging.getLogger(name)
            l.setLevel(target_level)
            for h in l.handlers:
                h.setLevel(target_level)
                
    return logging.getLevelName(target_level)


def get_recent_logs(lines: int = 100, level: str = None, search: str = None) -> list:
    """
    Read recent log lines from gtasks.log with optional level and keyword filtering.
    """
    log_file = get_log_file_path()
    if not log_file.exists():
        return []

    try:
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()

        if level:
            target = f" - {level.upper()} - "
            all_lines = [l for l in all_lines if target in l]

        if search:
            search_lower = search.lower()
            all_lines = [l for l in all_lines if search_lower in l.lower()]

        # Return latest N lines
        tail = all_lines[-lines:]
        return [l.rstrip('\r\n') for l in tail]
    except Exception as e:
        return [f"Error reading log file: {e}"]


def clear_logs() -> bool:
    """Clear/truncate the main log file."""
    log_file = get_log_file_path()
    try:
        if log_file.exists():
            with open(log_file, 'w') as f:
                f.truncate(0)
        return True
    except Exception:
        return False