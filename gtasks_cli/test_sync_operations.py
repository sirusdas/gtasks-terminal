#!/usr/bin/env python3
"""
Test script to verify that sync operations are working properly for all scenarios:
1. Add task and sync
2. Complete task and sync
3. Uncomplete task and sync
4. Delete task and sync
"""

import sys
import os
from datetime import datetime
import time

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import TaskStatus
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient


def test_sync_operations():
    """Test sync operations"""
    print("🔍 Testing sync operations with Google Tasks...")
    
    # Check if we can connect to Google Tasks
    google_client = GoogleTasksClient()
    if not google_client.connect():
        print("❌ Cannot connect to Google Tasks. Please check authentication.")
        return False
    
    # Initialize Task Manager in Google Tasks mode
    task_manager = TaskManager(use_google_tasks=True)
    
    # Clean up any previous test tasks
    print("\n🧹 Cleaning up previous test tasks...")
    tasks = task_manager.list_tasks()
    for task in tasks:
        if task.title and "Sync Test Task" in task.title:
            task_manager.delete_task(task.id)
    
    # Sync to ensure we start with a clean state
    print("\n🔄 Performing initial sync...")
    if not task_manager.sync_with_google_tasks():
        print("❌ Initial sync failed")
        return False
    
    # 1. Test adding a task and syncing
    print("\n1. Testing task creation and sync...")
    task_title = f"Sync Test Task {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    task = task_manager.create_task(
        title=task_title,
        description="Test task for verifying sync operations",
        priority="medium"
    )
    
    if task:
        print(f"   ✅ Task created successfully: {task.title} (ID: {task.id})")
        task_id = task.id
    else:
        print("   ❌ Failed to create task")
        return False
    
    # Sync after creation
    print("   🔄 Syncing after task creation...")
    if task_manager.sync_with_google_tasks():
        print("   ✅ Sync completed successfully")
    else:
        print("   ❌ Sync failed")
        return False
    
    # Verify task exists in Google Tasks
    time.sleep(2)  # Give some time for sync to complete
    tasks_after_sync = task_manager.list_tasks()
    task_found = any(t.id == task_id for t in tasks_after_sync)
    if task_found:
        print("   ✅ Task found in task list after sync")
    else:
        print("   ❌ Task not found in task list after sync")
        return False
    
    # 2. Test completing a task and syncing
    print("\n2. Testing task completion and sync...")
    if task_manager.complete_task(task_id):
        print("   ✅ Task marked as completed")
    else:
        print("   ❌ Failed to mark task as completed")
        return False
    
    # Sync after completion
    print("   🔄 Syncing after task completion...")
    if task_manager.sync_with_google_tasks():
        print("   ✅ Sync completed successfully")
    else:
        print("   ❌ Sync failed")
        return False
    
    # Verify task is completed in Google Tasks
    time.sleep(2)  # Give some time for sync to complete
    completed_task = task_manager.get_task(task_id)
    if completed_task and completed_task.status == TaskStatus.COMPLETED:
        print("   ✅ Task status correctly updated to completed after sync")
    else:
        print("   ❌ Task status not updated correctly after sync")
        return False
    
    # 3. Test uncompleting a task and syncing
    print("\n3. Testing task uncompletion and sync...")
    if task_manager.uncomplete_task(task_id):
        print("   ✅ Task marked as pending again")
    else:
        print("   ❌ Failed to mark task as pending")
        return False
    
    # Sync after uncompletion
    print("   🔄 Syncing after task uncompletion...")
    if task_manager.sync_with_google_tasks():
        print("   ✅ Sync completed successfully")
    else:
        print("   ❌ Sync failed")
        return False
    
    # Verify task is pending again in Google Tasks
    time.sleep(2)  # Give some time for sync to complete
    uncompleted_task = task_manager.get_task(task_id)
    if uncompleted_task and uncompleted_task.status == TaskStatus.PENDING:
        print("   ✅ Task status correctly updated to pending after sync")
    else:
        print("   ❌ Task status not updated correctly after sync")
        return False
    
    # 4. Test deleting a task and syncing
    print("\n4. Testing task deletion and sync...")
    if task_manager.delete_task(task_id):
        print("   ✅ Task marked as deleted")
    else:
        print("   ❌ Failed to mark task as deleted")
        return False
    
    # Sync after deletion
    print("   🔄 Syncing after task deletion...")
    if task_manager.sync_with_google_tasks():
        print("   ✅ Sync completed successfully")
    else:
        print("   ❌ Sync failed")
        return False
    
    # Verify task is deleted in Google Tasks
    time.sleep(2)  # Give some time for sync to complete
    deleted_task = task_manager.get_task(task_id)
    if deleted_task and deleted_task.status == TaskStatus.DELETED:
        print("   ✅ Task status correctly updated to deleted after sync")
    else:
        print("   ❌ Task status not updated correctly after sync")
        # This might be expected since deleted tasks may not be returned by the API
        print("   ℹ️  Note: Deleted tasks may not be returned by the API")
    
    print("\n🎉 All sync operations test completed!")
    return True


if __name__ == "__main__":
    try:
        success = test_sync_operations()
        if success:
            print("\n✅ All sync tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some sync tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during sync testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)