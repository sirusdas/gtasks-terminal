#!/usr/bin/env python3
"""
Simple debug test to see what's happening with duplicate detection.
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


def debug_simple():
    """Simple debug test."""
    print("Debug simple test...")
    
    # Initialize task manager in Google Tasks mode
    tm = TaskManager(use_google_tasks=True)
    
    # Generate a unique task title
    task_title = f"Simple Debug Test - {uuid.uuid4()}"
    
    print(f"1. Creating task: {task_title}")
    task1 = tm.create_task(
        title=task_title,
        description="Simple debug test task",
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
    
    print(f"2. Attempting to create duplicate task: {task_title}")
    task2 = tm.create_task(
        title=task_title,
        description="Simple debug test task",
        due=datetime.now() + timedelta(days=1),
        priority="high"
    )
    
    if task2 is None:
        print("✓ Duplicate task correctly skipped")
        return True
    elif task2.id == task1.id:
        print("✓ Same task returned (not duplicated)")
        return True
    else:
        print(f"✗ Duplicate task was created: {task2.title} (ID: {task2.id})")
        return False


if __name__ == "__main__":
    try:
        success = debug_simple()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error during debug: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)