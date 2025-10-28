#!/usr/bin/env python3
"""
Debug script for task creation process.
"""

import sys
import os

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Priority


def test_task_creation():
    """Test task creation process."""
    print("Testing task creation...")
    
    # Create task manager
    tm = TaskManager()
    print("TaskManager created")
    
    # Create a task
    task = tm.create_task(
        title="Debug Task",
        description="This is a debug task",
        priority=Priority.CRITICAL
    )
    print(f"Created task: {task.title} (ID: {task.id})")
    
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
    test_task_creation()