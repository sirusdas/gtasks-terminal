#!/usr/bin/env python3
"""
Simple test script to verify basic task operations work correctly with sync.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Task, TaskStatus, Priority


def test_simple_operations():
    """Test basic task operations with sync."""
    print("Testing basic task operations with sync...")
    
    # Initialize task manager in Google Tasks mode
    tm = TaskManager(use_google_tasks=True)
    
    # Generate a unique task title to avoid conflicts
    task_title = f"Simple Test Task - {uuid.uuid4()}"
    
    # Test 1: Add a task
    print(f"\n1. Testing task creation: {task_title}")
    task = tm.create_task(
        title=task_title,
        description="This is a simple test task for sync verification",
        due=datetime.now() + timedelta(days=1),
        priority=Priority.HIGH
    )
    
    if task:
        print(f"✓ Created task: {task.title} (ID: {task.id})")
        task_id = task.id
    else:
        print("✗ Failed to create task")
        return False
    
    # Give some time for sync
    import time
    time.sleep(2)
    
    # Test 2: Complete the task
    print("\n2. Testing task completion...")
    if tm.complete_task(task_id):
        print("✓ Task marked as completed")
    else:
        print("✗ Failed to complete task")
        return False
    
    # Give some time for sync
    time.sleep(2)
    
    # Test 3: Uncomplete the task
    print("\n3. Testing task uncompletion...")
    if tm.uncomplete_task(task_id):
        print("✓ Task marked as pending")
    else:
        print("✗ Failed to uncomplete task")
        return False
    
    # Give some time for sync
    time.sleep(2)
    
    # Test 4: Delete the task
    print("\n4. Testing task deletion...")
    if tm.delete_task(task_id):
        print("✓ Task marked as deleted")
    else:
        print("✗ Failed to delete task")
        return False
    
    # Give some time for sync
    time.sleep(2)
    
    print("\n✅ All basic operations completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = test_simple_operations()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)