"""
Storage module for the Google Tasks CLI application.
"""

# Import storage classes so they're available when importing from gtasks_cli.storage
from .local_storage import LocalStorage
from .sqlite_storage import SQLiteStorage  # Make SQLiteStorage available

__all__ = ['LocalStorage', 'SQLiteStorage']