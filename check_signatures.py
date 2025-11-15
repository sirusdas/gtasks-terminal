#!/usr/bin/env python3

import sys
import os
import hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.utils.task_deduplication import create_task_signature

def check_apple_signatures():
    """Check the signatures of apple tasks."""
    # These are the apple tasks we have locally
    apple_tasks = [
        {"title": "apple", "description": "", "due": "", "status": "pending"},
        {"title": "apple", "description": "", "due": "", "status": "pending"},
        {"title": "apple", "description": "", "due": "", "status": "pending"}
    ]
    
    signatures = set()
    for i, task in enumerate(apple_tasks):
        signature = create_task_signature(
            title=task["title"],
            description=task["description"],
            due_date=task["due"],
            status=task["status"]
        )
        signatures.add(signature)
        print(f"Apple task {i+1} signature: {signature}")
    
    print(f"\nUnique signatures: {len(signatures)}")
    
    # Check what signatures we have in Google Tasks
    print("\nChecking Google Tasks signatures...")
    from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
    from gtasks_cli.integrations.google_auth import GoogleAuthManager
    
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
    google_signatures = set()
    
    for tasklist in tasklists:
        if tasklist.get('title') == 'My Tasks':
            print(f"Checking tasklist: {tasklist.get('title')}")
            tasks = client.list_tasks(tasklist_id=tasklist['id'])
            for task in tasks:
                if task.title == 'apple':
                    signature = create_task_signature(
                        title=task.title or "",
                        description=task.description or "",
                        due_date=task.due,
                        status=task.status
                    )
                    google_signatures.add(signature)
                    print(f"  Found apple task - ID: {task.id}, Signature: {signature}")
            break
    
    print(f"\nGoogle Tasks apple signatures: {len(google_signatures)}")

if __name__ == "__main__":
    check_apple_signatures()