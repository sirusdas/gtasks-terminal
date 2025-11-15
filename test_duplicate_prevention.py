#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.utils.task_deduplication import create_task_signature, get_existing_task_signatures
from gtasks_cli.models.task import Task

def test_duplicate_detection():
    """Test the duplicate detection functionality."""
    print("Testing duplicate detection functionality...")
    
    # Use the personal account which seems to be the default
    client = GoogleTasksClient(account_name="personal")
    if not client.connect():
        print("Failed to connect to Google Tasks")
        return
    
    print("Connected to Google Tasks successfully")
    
    # Get existing task signatures
    print("Retrieving existing task signatures...")
    existing_signatures = get_existing_task_signatures(use_google_tasks=True)
    print(f"Found {len(existing_signatures)} existing task signatures")
    
    # Check for "Som Das" task signature
    som_das_signature = create_task_signature(
        title="Som Das",
        description="my babu",
        due_date="",
        status="needsAction"
    )
    
    print(f"Som Das task signature: {som_das_signature}")
    
    if som_das_signature in existing_signatures:
        print("✓ Som Das task signature found in existing signatures - duplicate detection working")
    else:
        print("✗ Som Das task signature NOT found in existing signatures")
    
    # Test with a new task
    new_task_signature = create_task_signature(
        title="Test Task - Unique",
        description="This is a unique test task",
        due_date="2025-12-31T00:00:00",
        status="needsAction"
    )
    
    print(f"New task signature: {new_task_signature}")
    
    if new_task_signature in existing_signatures:
        print("✗ New task signature found in existing signatures - this should not happen")
    else:
        print("✓ New task signature NOT found in existing signatures - correct behavior")

def count_som_das_before_after_sync():
    """Count Som Das tasks before and after a sync operation."""
    print("\nCounting Som Das tasks before sync...")
    
    # Use the personal account which seems to be the default
    client = GoogleTasksClient(account_name="personal")
    if not client.connect():
        print("Failed to connect to Google Tasks")
        return
    
    tasklists = client.list_tasklists()
    som_das_count_before = 0
    
    for tasklist in tasklists:
        if tasklist['title'] == 'My Tasks':
            print(f"Checking tasklist: {tasklist['title']}")
            tasks = client.list_tasks(
                tasklist_id=tasklist['id'], 
                show_completed=True, 
                show_hidden=True, 
                show_deleted=False
            )
            
            for task in tasks:
                if task.title == 'Som Das':
                    som_das_count_before += 1
    
    print(f"Som Das tasks before sync: {som_das_count_before}")
    
    # Here you would perform the sync operation
    print("Performing sync operation...")
    # This is where you would call your sync function
    
    # Count after sync
    print("Counting Som Das tasks after sync...")
    # You would repeat the counting logic here
    
    print("Sync test completed")

if __name__ == "__main__":
    test_duplicate_detection()
    count_som_das_before_after_sync()