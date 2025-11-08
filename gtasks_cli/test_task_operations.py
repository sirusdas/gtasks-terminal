#!/usr/bin/env python3
"""
Test script to verify that basic task operations are working properly:
1. Add task
2. Complete task
3. Uncomplete task
4. Delete task
"""

import sys
import os
from datetime import datetime

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import TaskStatus


def test_task_operations():
    """Test basic task operations"""
    print("🔍 Testing basic task operations...")
    
    # Initialize Task Manager in local mode
    task_manager = TaskManager(use_google_tasks=False)
    
    # Clean up any previous test tasks
    tasks = task_manager.list_tasks()
    for task in tasks:
        if task.title and "Test Task" in task.title:
            task_manager.delete_task(task.id)
    
    # 1. Test adding a task
    print("\n1. Testing task creation...")
    task_title = f"Test Task {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    task = task_manager.create_task(
        title=task_title,
        description="Test task for verifying operations",
        priority="medium"
    )
    
    if task:
        print(f"   ✅ Task created successfully: {task.title} (ID: {task.id})")
        task_id = task.id
    else:
        print("   ❌ Failed to create task")
        return False
    
    # Verify task was added
    tasks = task_manager.list_tasks()
    task_found = any(t.id == task_id for t in tasks)
    if task_found:
        print("   ✅ Task found in task list")
    else:
        print("   ❌ Task not found in task list")
        return False
    
    # 2. Test completing a task
    print("\n2. Testing task completion...")
    if task_manager.complete_task(task_id):
        print("   ✅ Task marked as completed")
    else:
        print("   ❌ Failed to mark task as completed")
        return False
    
    # Verify task is completed
    completed_task = task_manager.get_task(task_id)
    if completed_task and completed_task.status == TaskStatus.COMPLETED:
        print("   ✅ Task status correctly updated to completed")
    else:
        print("   ❌ Task status not updated correctly")
        return False
    
    # 3. Test uncompleting a task
    print("\n3. Testing task uncompletion...")
    if task_manager.uncomplete_task(task_id):
        print("   ✅ Task marked as pending again")
    else:
        print("   ❌ Failed to mark task as pending")
        return False
    
    # Verify task is pending again
    uncompleted_task = task_manager.get_task(task_id)
    if uncompleted_task and uncompleted_task.status == TaskStatus.PENDING:
        print("   ✅ Task status correctly updated to pending")
    else:
        print("   ❌ Task status not updated correctly")
        return False
    
    # 4. Test deleting a task
    print("\n4. Testing task deletion...")
    if task_manager.delete_task(task_id):
        print("   ✅ Task marked as deleted")
    else:
        print("   ❌ Failed to mark task as deleted")
        return False
    
    # Verify task is deleted
    deleted_task = task_manager.get_task(task_id)
    if deleted_task and deleted_task.status == TaskStatus.DELETED:
        print("   ✅ Task status correctly updated to deleted")
    else:
        print("   ❌ Task status not updated correctly")
        return False
    
    print("\n🎉 All basic task operations are working properly!")
    return True


if __name__ == "__main__":
    try:
        success = test_task_operations()
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during testing: {e}")
        sys.exit(1)