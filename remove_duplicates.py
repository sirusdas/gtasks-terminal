#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.utils.task_deduplication import create_task_signature

def remove_som_das_duplicates():
    """Remove duplicate Som Das tasks from Google Tasks."""
    print("Removing duplicate Som Das tasks...")
    
    # Use the personal account which seems to be the default
    config_dir = os.path.join(os.path.expanduser("~"), ".gtasks")
    credentials_file = os.path.join(config_dir, "credentials.json")
    token_file = os.path.join(config_dir, "token.pickle")
    
    client = GoogleTasksClient(credentials_file=credentials_file, token_file=token_file)
    if not client.connect():
        print("Failed to connect to Google Tasks")
        return
    
    tasklists = client.list_tasklists()
    som_das_tasks = []
    
    # Find all Som Das tasks
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
                    som_das_tasks.append({
                        'id': task.id,
                        'tasklist_id': tasklist['id'],
                        'modified_at': task.modified_at,
                        'created_at': task.created_at
                    })
                    print(f"  Found Som Das task - ID: {task.id}")
    
    print(f"\nTotal 'Som Das' tasks found: {len(som_das_tasks)}")
    
    if len(som_das_tasks) <= 1:
        print("No duplicates to remove")
        return
    
    # Sort by creation time, keep the oldest, remove the rest
    som_das_tasks.sort(key=lambda x: x['created_at'] if x['created_at'] else x['modified_at'])
    
    # Keep the first (oldest) task, remove the rest
    tasks_to_remove = som_das_tasks[1:]  # All but the first one
    
    print(f"\nRemoving {len(tasks_to_remove)} duplicate tasks...")
    
    removed_count = 0
    failed_count = 0
    
    for task_info in tasks_to_remove:
        try:
            print(f"  Removing task ID: {task_info['id']}")
            success = client.delete_task(task_info['id'], tasklist_id=task_info['tasklist_id'])
            if success:
                print(f"    Successfully removed task {task_info['id']}")
                removed_count += 1
            else:
                print(f"    Failed to remove task {task_info['id']}")
                failed_count += 1
        except Exception as e:
            print(f"    Exception while removing task {task_info['id']}: {e}")
            failed_count += 1
    
    print(f"\nRemoval summary: {removed_count} removed, {failed_count} failed")

if __name__ == "__main__":
    remove_som_das_duplicates()