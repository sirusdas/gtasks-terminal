#!/usr/bin/env python3
"""
Test script for TaskManager.
"""

import sys
import os

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Priority


def test_task_manager():
    """Test TaskManager functionality."""
    print("Testing TaskManager...")
    
    # Create task manager
    tm = TaskManager()
    print("TaskManager created")
    
    # Create a task
    task = tm.create_task(
        title="Test Task",
        description="This is a test task",
        priority=Priority.HIGH
    )
    print(f"Created task: {task.title} (ID: {task.id})")
    
    # List tasks
    tasks = tm.list_tasks()
    print(f"Total tasks: {len(tasks)}")
    
    # Get specific task
    retrieved_task = tm.get_task(task.id)
    print(f"Retrieved task: {retrieved_task.title}")
    
    print("All tests passed!")


if __name__ == "__main__":
    test_task_manager()