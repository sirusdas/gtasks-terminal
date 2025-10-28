#!/usr/bin/env python3
"""
Debug script for task creation process step by step.
"""

import sys
import os

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Priority


def test_task_creation_step_by_step():
    """Test task creation process step by step."""
    print("Testing task creation step by step...")
    
    # Create task manager
    tm = TaskManager()
    print("TaskManager created")
    
    # Load tasks first
    tasks_before = tm._load_tasks()
    print(f"Tasks before creation: {len(tasks_before)}")
    
    # Create a task
    task = tm.create_task(
        title="Step-by-step Task",
        description="This is a step-by-step task",
        priority=Priority.HIGH
    )
    print(f"Created task: {task.title} (ID: {task.id})")
    
    # Load tasks after creation
    tasks_after = tm._load_tasks()
    print(f"Tasks after creation: {len(tasks_after)}")
    
    # Check if file exists
    import os
    file_path = os.path.expanduser("~/.gtasks/tasks.json")
    print(f"File exists: {os.path.exists(file_path)}")
    if os.path.exists(file_path):
        print(f"File size: {os.path.getsize(file_path)} bytes")
        
        # Read file contents
        with open(file_path, 'r') as f:
            content = f.read()
            print(f"File content length: {len(content)} characters")
    
    print("Test completed!")


if __name__ == "__main__":
    test_task_creation_step_by_step()