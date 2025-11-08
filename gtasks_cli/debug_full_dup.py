#!/usr/bin/env python3
"""
Full debug script for duplicate detection.
"""

import sys
import os
import uuid
import logging
from datetime import datetime, timedelta

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.utils.task_deduplication import is_task_duplicate, get_existing_task_signatures, create_task_signature


def debug_full_dup():
    """Debug full duplicate detection."""
    print("Debugging full duplicate detection...")
    
    # Initialize task manager in Google Tasks mode
    tm = TaskManager(use_google_tasks=True)
    
    # Generate a unique task title
    task_title = f"Full Debug Test Task - {uuid.uuid4()}"
    task_description = "Full debug test task"
    task_due = datetime.now() + timedelta(days=1)
    task_status = "pending"
    
    print(f"\n1. Creating task: {task_title}")
    
    # Create the task
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
    
    print(f"\n2. Checking for duplicate after creation")
    
    # Get existing signatures
    existing_signatures = get_existing_task_signatures(use_google_tasks=True)
    print(f"Found {len(existing_signatures)} existing task signatures")
    
    # Create signature for our task
    task_signature = create_task_signature(
        task_title, 
        task_description, 
        str(task_due), 
        task_status
    )
    print(f"Created signature for our task: {task_signature}")
    
    # Check if task is in existing signatures
    is_in_signatures = task_signature in existing_signatures
    print(f"Task signature in existing signatures: {is_in_signatures}")
    
    # Use the is_task_duplicate function
    is_dup = is_task_duplicate(
        task_title=task_title,
        task_description=task_description,
        task_due_date=str(task_due),
        task_status=task_status,
        existing_signatures=existing_signatures,
        use_google_tasks=True
    )
    
    print(f"is_task_duplicate result: {is_dup}")
    
    print("\n✅ Full debug completed")
    return True


if __name__ == "__main__":
    try:
        debug_full_dup()
    except Exception as e:
        print(f"Error during debug: {e}")
        import traceback
        traceback.print_exc()