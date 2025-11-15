#!/usr/bin/env python3

import sys
import os
import sqlite3
from typing import List

# Add the project src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.integrations.google_auth import GoogleAuthManager
from gtasks_cli.utils.task_deduplication import create_task_signature
from gtasks_cli.models.task import Task

def remove_local_apple_duplicates():
    """Remove duplicate apple tasks from local database, keeping only one."""
    print("Removing duplicate apple tasks from local database...")
    
    # Connect to the local database
    db_path = "/Users/int/.gtasks/personal/tasks.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all apple tasks
    cursor.execute("SELECT id, title, description, notes FROM tasks WHERE title='apple'")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} local apple tasks")
    
    if len(rows) <= 1:
        print("No duplicates to remove locally")
        conn.close()
        return
    
    # Keep the first one and delete the rest
    ids_to_delete = [row[0] for row in rows[1:]]  # All except the first
    
    for task_id in ids_to_delete:
        cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        print(f"Deleted local apple task with ID: {task_id}")
    
    conn.commit()
    conn.close()
    
    print(f"Removed {len(ids_to_delete)} duplicate apple tasks from local database")

def remove_remote_apple_duplicates():
    """Remove duplicate apple tasks from Google Tasks, keeping only one."""
    print("Removing duplicate apple tasks from Google Tasks...")
    
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
                    'tasklist_id': tasklist['id']
                })
    
    print(f"Found {len(apple_tasks)} remote apple tasks")
    
    if len(apple_tasks) <= 1:
        print("No duplicates to remove remotely")
        return
    
    # Keep the first one and delete the rest
    tasks_to_delete = apple_tasks[1:]  # All except the first
    
    deleted_count = 0
    for item in tasks_to_delete:
        task = item['task']
        tasklist_id = item['tasklist_id']
        
        try:
            # Delete the task
            service.tasks().delete(tasklist=tasklist_id, task=task.id).execute()
            print(f"Deleted remote apple task with ID: {task.id}")
            deleted_count += 1
        except Exception as e:
            print(f"Failed to delete remote apple task {task.id}: {e}")
    
    print(f"Removed {deleted_count} duplicate apple tasks from Google Tasks")

def main():
    """Main function to remove apple duplicates."""
    print("Removing duplicate apple tasks...")
    print("=" * 40)
    
    # Remove local duplicates
    remove_local_apple_duplicates()
    
    print()
    
    # Remove remote duplicates
    remove_remote_apple_duplicates()
    
    print()
    print("Finished removing duplicate apple tasks!")

if __name__ == "__main__":
    main()