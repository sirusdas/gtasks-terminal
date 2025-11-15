#!/usr/bin/env python3

import sys
import os

# Add the project src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.integrations.google_auth import GoogleAuthManager

def check_remote_apple_tasks():
    """Check how many apple tasks we have in Google Tasks."""
    print("Checking remote apple tasks...")
    
    # Initialize Google Tasks client
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
    
    # Get all tasklists
    tasklists = client.list_tasklists()
    
    apple_tasks = []
    
    # Find all apple tasks across all tasklists
    for tasklist in tasklists:
        tasks = client.list_tasks(tasklist_id=tasklist['id'], show_completed=True)
        for task in tasks:
            if task.title == 'apple':
                apple_tasks.append({
                    'task': task,
                    'tasklist': tasklist['title']
                })
    
    print(f"Found {len(apple_tasks)} remote apple tasks:")
    for i, item in enumerate(apple_tasks):
        task = item['task']
        tasklist = item['tasklist']
        print(f"  {i+1}. ID: {task.id}, Tasklist: {tasklist}")
    
    return len(apple_tasks)

if __name__ == "__main__":
    count = check_remote_apple_tasks()
    print(f"\nTotal apple tasks in Google Tasks: {count}")