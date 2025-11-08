#!/usr/bin/env python3
"""
Test script to verify that sync doesn't create duplicate tasks.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Task, TaskStatus, Priority


def test_no_duplicate_sync():
    """Test that sync doesn't create duplicate tasks."""
    print("Testing sync without creating duplicates...")
    
    # Initialize task manager in Google Tasks mode
    tm = TaskManager(use_google_tasks=True)
    
    # Generate a unique task title to avoid conflicts
    task_title = f"NoDup Test Task - {uuid.uuid4()}"
    
    # Test 1: Add a task
    print(f"\n1. Creating task: {task_title}")
    task = tm.create_task(
        title=task_title,
        description="This is a test task to verify no duplicates are created during sync",
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
    
    # Test 2: List tasks to verify it exists only once
    print("\n2. Verifying task exists only once before sync...")
    tasks_before_sync = tm.list_tasks()
    found_tasks_before = [t for t in tasks_before_sync if t.title == task_title]
    
    if len(found_tasks_before) == 1:
        print(f"✓ Found task exactly once before sync: {found_tasks_before[0].title}")
    else:
        print(f"✗ Found {len(found_tasks_before)} instances of the task before sync")
        return False
    
    # Test 3: Force a sync operation
    print("\n3. Forcing sync operation...")
    tm.sync_manager.sync()
    
    # Give some time for sync
    time.sleep(2)
    
    # Test 4: List tasks again to verify it still exists only once
    print("\n4. Verifying task exists only once after sync...")
    tasks_after_sync = tm.list_tasks()
    found_tasks_after = [t for t in tasks_after_sync if t.title == task_title]
    
    if len(found_tasks_after) == 1:
        print(f"✓ Found task exactly once after sync: {found_tasks_after[0].title}")
        print("\n✅ Sync test passed - no duplicates created!")
        return True
    else:
        print(f"✗ Found {len(found_tasks_after)} instances of the task after sync")
        return False


if __name__ == "__main__":
    try:
        success = test_no_duplicate_sync()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)