#!/usr/bin/env python3
"""
Final test to verify the duplicate fix.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager


def test_duplicate_fix():
    """Test that duplicate task creation is fixed."""
    print("Testing duplicate task creation fix...")
    
    # Initialize task manager in Google Tasks mode
    tm = TaskManager(use_google_tasks=True)
    
    # Generate a unique task title to avoid conflicts
    task_title = f"Final Dup Fix Test Task - {uuid.uuid4()}"
    
    # Test 1: Add a task
    print(f"\n1. Creating task: {task_title}")
    task1 = tm.create_task(
        title=task_title,
        description="Final test task to verify duplicate fix",
        due=datetime.now() + timedelta(days=1),
        priority="high"
    )
    
    if task1:
        print(f"✓ Created first task: {task1.title} (ID: {task1.id})")
    else:
        print("✗ Failed to create first task")
        return False
    
    # Give some time for sync
    import time
    time.sleep(2)
    
    # Test 2: Try to create the same task again
    print(f"\n2. Attempting to create duplicate task: {task_title}")
    task2 = tm.create_task(
        title=task_title,
        description="Final test task to verify duplicate fix",
        due=datetime.now() + timedelta(days=1),
        priority="high"
    )
    
    if task2 is None:
        print("✓ Duplicate task correctly skipped")
        success = True
    elif task2.id == task1.id:
        print("✓ Same task returned (not duplicated)")
        success = True
    else:
        print(f"✗ Duplicate task was created: {task2.title} (ID: {task2.id})")
        success = False
    
    print("\n✅ Duplicate fix test completed")
    return success


if __name__ == "__main__":
    try:
        success = test_duplicate_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)