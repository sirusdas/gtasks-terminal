"""
TaskList model for the Google Tasks CLI application.
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class TaskList(BaseModel):
    """Represents a task list in Google Tasks or local storage."""
    
    id: str
    title: str
    updated: Optional[datetime] = None
    position: Optional[str] = None
    etag: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True