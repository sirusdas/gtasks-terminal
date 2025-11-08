#!/usr/bin/env python3
"""
Test script to verify that task operations work correctly with sync.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Task, TaskStatus, Priority


def test_sync_operations():
    """Test all task operations with sync."""
    print("Testing task operations with sync...")
    
    # Initialize task manager in Google Tasks mode
    tm = TaskManager(use_google_tasks=True)
    
    # Test 1: Add a task
    print("\n1. Testing task creation...")
    task_title = f"Test Task - {uuid.uuid4()}"
    task = tm.create_task(
        title=task_title,
        description="This is a test task for sync verification",
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
    
    # Test 2: List tasks to verify it exists
    print("\n2. Testing task retrieval...")
    tasks = tm.list_tasks()
    found_task = next((t for t in tasks if t.id == task_id), None)
    
    if found_task:
        print(f"✓ Found task in list: {found_task.title}")
    else:
        print("✗ Task not found in list")
        # Try again with show_deleted
        tasks = tm.list_tasks(show_deleted=True)
        found_task = next((t for t in tasks if t.id == task_id), None)
        if found_task:
            print(f"✓ Found task in list (including deleted): {found_task.title}")
        else:
            print("✗ Task not found even in deleted list")
            return False
    
    # Test 3: Complete the task
    print("\n3. Testing task completion...")
    if tm.complete_task(task_id):
        print("✓ Task marked as completed")
    else:
        print("✗ Failed to complete task")
        return False
    
    # Give some time for sync
    time.sleep(2)
    
    # Verify task is completed
    updated_tasks = tm.list_tasks(show_completed=True)
    completed_task = next((t for t in updated_tasks if t.id == task_id), None)
    
    if completed_task and completed_task.status == TaskStatus.COMPLETED:
        print("✓ Task completion verified")
    else:
        print("✗ Task completion not verified")
        return False
    
    # Test 4: Uncomplete the task
    print("\n4. Testing task uncompletion...")
    if tm.uncomplete_task(task_id):
        print("✓ Task marked as pending")
    else:
        print("✗ Failed to uncomplete task")
        return False
    
    # Give some time for sync
    time.sleep(2)
    
    # Verify task is pending
    updated_tasks = tm.list_tasks()
    pending_task = next((t for t in updated_tasks if t.id == task_id), None)
    
    if pending_task and pending_task.status == TaskStatus.PENDING:
        print("✓ Task uncompletion verified")
    else:
        print("✗ Task uncompletion not verified")
        return False
    
    # Test 5: Delete the task
    print("\n5. Testing task deletion...")
    if tm.delete_task(task_id):
        print("✓ Task marked as deleted")
    else:
        print("✗ Failed to delete task")
        return False
    
    # Give some time for sync
    time.sleep(2)
    
    # Verify task is deleted
    all_tasks = tm.list_tasks(show_deleted=True)
    deleted_task = next((t for t in all_tasks if t.id == task_id), None)
    
    if deleted_task and deleted_task.status == TaskStatus.DELETED:
        print("✓ Task deletion verified")
    else:
        print("✗ Task deletion not verified")
        return False
    
    print("\n✅ All sync operations passed!")
    return True


if __name__ == "__main__":
    try:
        success = test_sync_operations()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)