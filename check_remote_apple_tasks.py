#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.integrations.google_auth import GoogleAuthManager
from gtasks_cli.utils.task_deduplication import create_task_signature

def check_remote_apple_tasks():
    """Check the remote apple tasks."""
    client = GoogleTasksClient()
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
    
    for tasklist in tasklists:
        if tasklist.get('title') == 'My Tasks':
            print(f"Checking tasklist: {tasklist.get('title')}")
            tasks = client.list_tasks(tasklist_id=tasklist['id'])
            apple_tasks = [task for task in tasks if task.title == 'apple']
            
            print(f"Found {len(apple_tasks)} remote apple tasks")
            
            for i, task in enumerate(apple_tasks):
                print(f"\nRemote apple task {i+1}:")
                print(f"  ID: {task.id}")
                print(f"  Title: {task.title}")
                print(f"  Description: {task.description}")
                print(f"  Notes: {task.notes}")
                print(f"  Due: {task.due}")
                print(f"  Status: {task.status}")
                
                # Create signature
                signature = create_task_signature(
                    title=task.title or "",
                    description=task.description or "",
                    due_date=task.due,
                    status=task.status
                )
                print(f"  Signature: {signature}")
            break

if __name__ == "__main__":
    check_remote_apple_tasks()