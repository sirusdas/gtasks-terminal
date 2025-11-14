"""
Utility functions for datetime operations.
"""

from datetime import datetime


def _normalize_datetime(dt):
    """
    Normalize datetime to timezone-naive for comparison.
    
    Args:
        dt: datetime object that may or may not have timezone info
        
    Returns:
        datetime: timezone-naive datetime object
    """
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        # Convert to naive datetime by removing timezone info
        return dt.replace(tzinfo=None)
    return dt