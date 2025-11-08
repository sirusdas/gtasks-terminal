#!/usr/bin/env python3
"""
Debug script to test signature creation and comparison.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.utils.task_deduplication import create_task_signature


def debug_signatures():
    """Debug signature creation."""
    print("Debugging signature creation...")
    
    # Generate a unique task title
    task_title = f"Signature Test Task - {uuid.uuid4()}"
    task_description = "Signature test task"
    task_due = str(datetime.now() + timedelta(days=1))
    task_status = "pending"
    
    # Create signature
    signature = create_task_signature(task_title, task_description, task_due, task_status)
    print(f"Signature for test task: {signature}")
    print(f"Components: {task_title}|{task_description}|{task_due}|{task_status}")
    
    # Create signature with same components
    signature2 = create_task_signature(task_title, task_description, task_due, task_status)
    print(f"Signature for same task: {signature2}")
    print(f"Signatures match: {signature == signature2}")
    
    print("\n✅ Signature debug completed")


if __name__ == "__main__":
    try:
        debug_signatures()
    except Exception as e:
        print(f"Error during debug: {e}")
        import traceback
        traceback.print_exc()