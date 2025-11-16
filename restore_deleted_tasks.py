#!/usr/bin/env python3
"""
Script to restore tasks that were incorrectly marked as deleted during sync.
"""

import json
import sys
import os
from datetime import datetime

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Task, TaskStatus


def restore_deleted_tasks(account_name="personal"):
    """Restore tasks that were incorrectly marked as deleted."""
    
    # Load the deletion log
    deletion_log_path = os.path.expanduser(f"~/.gtasks/deletion_log.json")
    
    if not os.path.exists(deletion_log_path):
        print(f"Deletion log not found at {deletion_log_path}")
        return
    
    with open(deletion_log_path, 'r') as f:
        deletion_log = json.load(f)
    
    print(f"Found {len(deletion_log)} deleted tasks in the log")
    
    # Create task manager
    task_manager = TaskManager(storage_backend='sqlite', account_name=account_name)
    
    # Get current tasks
    current_tasks = task_manager.list_tasks()
    current_task_ids = {task.id for task in current_tasks}
    
    # Count how many tasks we'll restore
    tasks_to_restore = []
    for entry in deletion_log:
        task_id = entry.get("task_id")
        if task_id not in current_task_ids:
            # Task doesn't exist anymore, we can restore it
            tasks_to_restore.append(entry)
    
    print(f"Found {len(tasks_to_restore)} tasks that can be restored")
    
    if not tasks_to_restore:
        print("No tasks to restore")
        return
    
    # Confirm with user
    confirm = input(f"Do you want to restore {len(tasks_to_restore)} tasks? (y/N): ")
    if confirm.lower() != 'y':
        print("Restoration cancelled")
        return
    
    # Restore tasks
    restored_count = 0
    for entry in tasks_to_restore:
        try:
            # Create a new task with the same properties
            task = Task(
                id=entry["task_id"],
                title=entry["task_title"],
                description=entry.get("task_description"),
                due=datetime.fromisoformat(entry["task_due"]) if entry.get("task_due") else None,
                status=TaskStatus.PENDING,  # Restore as pending instead of deleted
                tasklist_id="default"  # Use default tasklist
            )
            
            # Add the task
            task_manager.create_task(
                title=task.title,
                description=task.description,
                due=task.due.isoformat() if task.due else None,
                tasklist_id=task.tasklist_id
            )
            
            restored_count += 1
            print(f"Restored task: {task.title}")
            
        except Exception as e:
            print(f"Failed to restore task {entry.get('task_title', 'Unknown')}: {e}")
    
    print(f"Restored {restored_count} tasks successfully")


if __name__ == "__main__":
    restore_deleted_tasks()