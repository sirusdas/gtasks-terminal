"""
Task model for the Google Tasks CLI application.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    DELETED = "deleted"


class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    due: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    project: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    parent_id: Optional[str] = None
    tasklist_id: str
    list_title: Optional[str] = None
    position: int = 0
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # minutes
    actual_duration: Optional[int] = None
    recurrence_rule: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)  # List of task IDs this task depends on
    is_recurring: bool = False  # Whether this is a recurring task template
    recurring_task_id: Optional[str] = None  # ID of the original recurring task template

    class Config:
        use_enum_values = True