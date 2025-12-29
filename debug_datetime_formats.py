#!/usr/bin/env python3

import sys
import os
from datetime import datetime, timezone
from gtasks_cli.storage.sqlite_storage import SQLiteStorage
from gtasks_cli.models.task import Task

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli/src'))

def debug_datetime_formats():
    """Debug the datetime formats in the actual database."""
    print("Debugging datetime formats in database...")
    
    # Load tasks from the database
    storage = SQLiteStorage(account_name="work")  # Use the same account as in the logs
    task_dicts = storage.load_tasks()
    
    print(f"Loaded {len(task_dicts)} tasks from database")
    
    # Check datetime formats for a few tasks
    for i, task_dict in enumerate(task_dicts[:5]):
        print(f"\nTask {i+1} ({task_dict.get('id', 'N/A')}):")
        print(f"  Title: {task_dict.get('title', 'N/A')}")
        
        # Check created_at
        created_at = task_dict.get('created_at')
        print(f"  created_at: {created_at} (type: {type(created_at)})")
        if isinstance(created_at, str):
            try:
                parsed = datetime.fromisoformat(created_at)
                print(f"    Parsed as: {parsed} (tzinfo: {parsed.tzinfo})")
            except Exception as e:
                print(f"    Failed to parse: {e}")
        
        # Check modified_at
        modified_at = task_dict.get('modified_at')
        print(f"  modified_at: {modified_at} (type: {type(modified_at)})")
        if isinstance(modified_at, str):
            try:
                parsed = datetime.fromisoformat(modified_at)
                print(f"    Parsed as: {parsed} (tzinfo: {parsed.tzinfo})")
            except Exception as e:
                print(f"    Failed to parse: {e}")

if __name__ == "__main__":
    debug_datetime_formats()