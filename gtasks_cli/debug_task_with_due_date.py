#!/usr/bin/env python3
"""
Debug script for creating a task with due date.
"""

import sys
import os

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Priority
from datetime import datetime


def test_task_with_due_date():
    """Test creating a task with due date."""
    print("Testing task creation with due date...")
    
    # Create task manager
    tm = TaskManager()
    print("TaskManager created")
    
    # Create a task with due date
    task = tm.create_task(
        title="Task with Due Date",
        description="This task has a due date",
        due="2024-12-31T15:30:00",
        priority=Priority.HIGH
    )
    print(f"Created task: {task.title} (ID: {task.id})")
    if task.due:
        print(f"Due date: {task.due}")
    
    # List tasks
    tasks = tm.list_tasks()
    print(f"Total tasks after creation: {len(tasks)}")
    
    # Check if file exists
    import os
    file_path = os.path.expanduser("~/.gtasks/tasks.json")
    print(f"File exists: {os.path.exists(file_path)}")
    if os.path.exists(file_path):
        print(f"File size: {os.path.getsize(file_path)} bytes")
    
    print("Test completed!")


if __name__ == "__main__":
    test_task_with_due_date()