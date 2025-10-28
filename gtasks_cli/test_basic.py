#!/usr/bin/env python3
"""
Simple test script to verify basic functionality of the Google Tasks CLI.
"""

import sys
import os

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Priority, TaskStatus


def test_task_manager():
    """Test basic TaskManager functionality."""
    print("Testing TaskManager...")
    
    # Create task manager
    tm = TaskManager()
    
    # Create a task
    task = tm.create_task(
        title="Test Task",
        description="This is a test task",
        priority=Priority.HIGH,
        project="Test Project"
    )
    
    print(f"Created task: {task.title} (ID: {task.id})")
    
    # List tasks
    tasks = tm.list_tasks()
    print(f"Total tasks: {len(tasks)}")
    
    # List tasks with filter
    high_priority_tasks = tm.list_tasks(priority=Priority.HIGH)
    print(f"High priority tasks: {len(high_priority_tasks)}")
    
    # Get specific task
    retrieved_task = tm.get_task(task.id)
    print(f"Retrieved task: {retrieved_task.title}")
    
    # Update task
    tm.update_task(task.id, title="Updated Test Task")
    updated_task = tm.get_task(task.id)
    print(f"Updated task title: {updated_task.title}")
    
    # Complete task
    tm.complete_task(task.id)
    completed_task = tm.get_task(task.id)
    print(f"Task status: {completed_task.status}")
    
    print("All tests passed!")


if __name__ == "__main__":
    test_task_manager()