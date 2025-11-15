#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient

def count_som_das_tasks():
    """Count the number of 'Som Das' tasks in Google Tasks."""
    # Use the personal account which seems to be the default
    config_dir = os.path.join(os.path.expanduser("~"), ".gtasks")
    credentials_file = os.path.join(config_dir, "credentials.json")
    token_file = os.path.join(config_dir, "token.pickle")
    
    client = GoogleTasksClient(credentials_file=credentials_file, token_file=token_file)
    if not client.connect():
        print("Failed to connect to Google Tasks")
        return
    
    tasklists = client.list_tasklists()
    som_das_count = 0
    som_das_tasks = []
    
    for tasklist in tasklists:
        if tasklist.get('title') == 'My Tasks':
            print(f"Checking tasklist: {tasklist.get('title')}")
            tasks = client.list_tasks(tasklist_id=tasklist['id'])
            for task in tasks:
                if task.title == 'Som Das':
                    print(f"  Found Som Das task - ID: {task.id}")
                    som_das_count += 1
                    som_das_tasks.append(task)
            break
    
    print(f"\nTotal 'Som Das' tasks found: {som_das_count}")

if __name__ == "__main__":
    count_som_das_tasks()