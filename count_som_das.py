#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.integrations.google_auth import GoogleAuthManager

def count_apple_tasks():
    """Count the number of 'apple' tasks in Google Tasks."""
    # Use the personal account which seems to be the default
    client = GoogleTasksClient()
    
    # Force a fresh authentication
    auth_manager = GoogleAuthManager()
    service = auth_manager.get_service()
    
    if not service:
        print("Failed to connect to Google Tasks")
        return
    
    client.service = service
    
    if not client.connect():
        print("Failed to connect to Google Tasks")
        return
    
    tasklists = client.list_tasklists()
    apple_count = 0
    apple_tasks = []
    
    for tasklist in tasklists:
        if tasklist.get('title') == 'My Tasks':
            print(f"Checking tasklist: {tasklist.get('title')}")
            tasks = client.list_tasks(tasklist_id=tasklist['id'])
            for task in tasks:
                if task.title == 'apple':
                    print(f"  Found apple task - ID: {task.id}")
                    apple_count += 1
                    apple_tasks.append(task)
            break
    
    print(f"\nTotal 'apple' tasks found: {apple_count}")

if __name__ == "__main__":
    count_apple_tasks()