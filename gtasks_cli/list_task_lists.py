#!/usr/bin/env python3
"""
Script to list all task lists in Google Tasks
"""

import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient


def list_task_lists():
    """List all task lists in Google Tasks."""
    print("🔍 Listing all task lists in Google Tasks...")
    
    # Initialize Google Tasks client
    google_client = GoogleTasksClient()
    
    if not google_client.connect():
        print("❌ Failed to connect to Google Tasks")
        return False
    
    # List all task lists
    task_lists = google_client.list_tasklists()
    
    total_tasks = 0
    print(f"📋 Found {len(task_lists)} task list(s):")
    for task_list in task_lists:
        print(f"  - {task_list['title']} (ID: {task_list['id']})")
        # List tasks in this task list
        tasks = google_client.list_tasks(tasklist_id=task_list['id'])
        print(f"    Tasks: {len(tasks)}")
        total_tasks += len(tasks)
    
    print(f"\n📊 Total tasks across all lists: {total_tasks}")
    return True


if __name__ == "__main__":
    list_task_lists()