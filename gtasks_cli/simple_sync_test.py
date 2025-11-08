#!/usr/bin/env python3
"""
Simple test to verify that sync operations are working
"""

import sys
import os
from datetime import datetime

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import TaskStatus


def test_sync_operations():
    """Test sync operations"""
    print("🔍 Testing sync operations...")
    
    # Initialize Task Manager in Google Tasks mode
    task_manager = TaskManager(use_google_tasks=True)
    
    # Test 1: Add task
    print("\n1. Testing task creation...")
    task_title = f"Sync Test {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    task = task_manager.create_task(
        title=task_title,
        description="Test task for sync verification",
        priority="medium"
    )
    
    if task:
        print(f"   ✅ Task created: {task.title} (ID: {task.id})")
        task_id = task.id
    else:
        print("   ❌ Failed to create task")
        return False
    
    # Test 2: Complete task
    print("\n2. Testing task completion...")
    if task_manager.complete_task(task_id):
        print("   ✅ Task marked as completed")
    else:
        print("   ❌ Failed to mark task as completed")
        return False
    
    # Test 3: Uncomplete task
    print("\n3. Testing task uncompletion...")
    if task_manager.uncomplete_task(task_id):
        print("   ✅ Task marked as pending again")
    else:
        print("   ❌ Failed to mark task as pending")
        return False
    
    # Test 4: Delete task
    print("\n4. Testing task deletion...")
    if task_manager.delete_task(task_id):
        print("   ✅ Task marked as deleted")
    else:
        print("   ❌ Failed to mark task as deleted")
        return False
    
    # Test 5: Sync
    print("\n5. Testing sync...")
    if task_manager.sync_with_google_tasks():
        print("   ✅ Sync completed successfully")
    else:
        print("   ❌ Sync failed")
        return False
    
    print("\n🎉 All sync operations completed!")
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