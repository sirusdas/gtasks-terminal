#!/usr/bin/env python3
"""
Direct test script for deduplication functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
import hashlib
from collections import defaultdict


def create_task_signature(task):
    """Create a signature for a task based on its key attributes"""
    signature_parts = [
        str(task.title or ''),
        str(task.description or ''),
        str(task.due) if task.due else '',
        str(task.status.value) if hasattr(task.status, 'value') else str(task.status)
    ]
    
    signature_string = '|'.join(signature_parts)
    return hashlib.md5(signature_string.encode('utf-8')).hexdigest()


def main():
    """Test deduplication functionality directly"""
    print("🗑️ Removing duplicate tasks...")
    
    # Connect to Google Tasks
    google_client = GoogleTasksClient()
    if not google_client.connect():
        print("❌ Failed to connect to Google Tasks")
        return 1
    
    print("✅ Connected to Google Tasks API")
    
    # Get all task lists
    tasklists = google_client.list_tasklists()
    print(f"Found {len(tasklists)} task lists")
    
    total_duplicates = 0
    total_removed = 0
    total_errors = 0
    
    for tasklist in tasklists:
        tasklist_id = tasklist['id']
        tasklist_title = tasklist['title']
        
        print(f"\nProcessing '{tasklist_title}' list...")
        
        # Get all tasks (including deleted) from this list
        all_tasks = google_client.list_tasks(
            tasklist_id=tasklist_id,
            show_completed=True,
            show_hidden=True,
            show_deleted=True
        )
        
        print(f"  Total tasks in list: {len(all_tasks)}")
        
        # Group tasks by signature
        task_groups = defaultdict(list)
        for task in all_tasks:
            signature = create_task_signature(task)
            task_groups[signature].append(task)
        
        print(f"  Grouped tasks into {len(task_groups)} signature groups")
        
        # Find duplicates (groups with more than one task)
        duplicates = []
        duplicate_groups = 0
        for signature, tasks in task_groups.items():
            if len(tasks) > 1:
                print(f"  Found duplicate group with {len(tasks)} tasks")
                duplicate_groups += 1
                # Sort by modification date to keep the most recent one
                tasks.sort(key=lambda t: t.modified_at or t.created_at, reverse=True)
                # Keep the first (most recent) and mark others for deletion
                duplicates.extend(tasks[1:])
        
        print(f"  Found {len(duplicates)} duplicate tasks in {duplicate_groups} groups")
        total_duplicates += len(duplicates)
        
        if duplicates:
            print("  Duplicates to be removed:")
            for i, task in enumerate(duplicates):
                mod_date = task.modified_at or task.created_at
                print(f"    {i+1}. {task.title} (ID: {task.id}, Modified: {mod_date})")
            
            # Remove duplicates
            removed_count = 0
            failed_count = 0
            
            for task in duplicates:
                try:
                    print(f"    Deleting task: {task.title} (ID: {task.id})")
                    # Delete the task
                    success = google_client.delete_task(task.id, tasklist_id=tasklist_id)
                    if success:
                        print(f"    Successfully deleted task: {task.title}")
                        removed_count += 1
                    else:
                        print(f"    Failed to delete task: {task.title}")
                        failed_count += 1
                except Exception as e:
                    print(f"    Failed to remove {task.title}: {e}")
                    failed_count += 1
            
            print(f"  Removed: {removed_count}, Failed: {failed_count}")
            total_removed += removed_count
            total_errors += failed_count
        else:
            print("  No duplicates found in this list")
    
    print(f"\n📊 Removal Summary:")
    print(f"   Total duplicate tasks found: {total_duplicates}")
    print(f"   Successfully removed: {total_removed}")
    print(f"   Failed to remove: {total_errors}")
    
    if total_removed > 0:
        print("\n✅ Duplicate removal completed.")
        print("You may want to run 'gtasks sync' to ensure consistency.")
    else:
        print("\n✅ No duplicates found or removed.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())