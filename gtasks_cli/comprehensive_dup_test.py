#!/usr/bin/env python3
"""
Comprehensive test for duplicate detection.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.utils.task_deduplication import is_task_duplicate, get_existing_task_signatures


def comprehensive_duplicate_test():
    """Comprehensive test for duplicate detection."""
    print("Comprehensive duplicate detection test...")
    
    # Initialize task manager in Google Tasks mode
    tm = TaskManager(use_google_tasks=True)
    
    # Generate a unique task title
    task_title = f"Comprehensive Test Task - {uuid.uuid4()}"
    task_description = "Comprehensive test task for duplicate detection"
    task_due = datetime.now() + timedelta(days=1)
    
    # Check if task exists before creation
    print(f"\n1. Checking for existing task before creation: {task_title}")
    existing_signatures = get_existing_task_signatures(use_google_tasks=True)
    print(f"Found {len(existing_signatures)} existing task signatures")
    
    is_dup_before = is_task_duplicate(
        task_title=task_title,
        task_description=task_description,
        task_due_date=str(task_due),
        task_status="pending",
        existing_signatures=existing_signatures,
        use_google_tasks=True
    )
    
    print(f"Is duplicate before creation: {is_dup_before}")
    
    # Create the task
    print(f"\n2. Creating task: {task_title}")
    task = tm.create_task(
        title=task_title,
        description=task_description,
        due=task_due,
        priority="high"
    )
    
    if task:
        print(f"✓ Created task: {task.title} (ID: {task.id})")
    else:
        print("✗ Failed to create task")
        return False
    
    # Give some time for sync
    import time
    time.sleep(2)
    
    # Check if task is detected as duplicate after creation
    print(f"\n3. Checking for duplicate after creation: {task_title}")
    existing_signatures_after = get_existing_task_signatures(use_google_tasks=True)
    print(f"Found {len(existing_signatures_after)} existing task signatures after creation")
    
    is_dup_after = is_task_duplicate(
        task_title=task_title,
        task_description=task_description,
        task_due_date=str(task_due),
        task_status="pending",
        existing_signatures=existing_signatures_after,
        use_google_tasks=True
    )
    
    print(f"Is duplicate after creation: {is_dup_after}")
    
    # Try to create the same task again
    print(f"\n4. Attempting to create duplicate task: {task_title}")
    task2 = tm.create_task(
        title=task_title,
        description=task_description,
        due=task_due,
        priority="high"
    )
    
    if task2 is None:
        print("✓ Duplicate task correctly skipped")
        result = True
    else:
        print(f"✗ Duplicate task was created: {task2.title} (ID: {task2.id})")
        result = False
    
    print("\n✅ Comprehensive test completed")
    return result


if __name__ == "__main__":
    try:
        success = comprehensive_duplicate_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)