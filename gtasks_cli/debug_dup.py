#!/usr/bin/env python3
"""
Debug script to test duplicate detection.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.utils.task_deduplication import is_task_duplicate, get_existing_task_signatures


def debug_duplicate_detection():
    """Debug duplicate detection."""
    print("Debugging duplicate detection...")
    
    # Generate a unique task title
    task_title = f"Debug Test Task - {uuid.uuid4()}"
    
    # Check if task exists before creation
    print(f"\n1. Checking for existing task: {task_title}")
    existing_signatures = get_existing_task_signatures(use_google_tasks=True)
    print(f"Found {len(existing_signatures)} existing task signatures")
    
    is_dup = is_task_duplicate(
        task_title=task_title,
        task_description="Debug test task",
        task_due_date=str(datetime.now() + timedelta(days=1)),
        task_status="pending",
        existing_signatures=existing_signatures,
        use_google_tasks=True
    )
    
    print(f"Is duplicate before creation: {is_dup}")
    
    print("\n✅ Debug test completed")


if __name__ == "__main__":
    try:
        debug_duplicate_detection()
    except Exception as e:
        print(f"Error during debug: {e}")
        import traceback
        traceback.print_exc()