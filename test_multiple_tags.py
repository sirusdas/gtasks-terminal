#!/usr/bin/env python3
"""
Test script to verify that tasks with multiple tags appear in all matching categories
"""

import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.reports.organized_tasks_report import OrganizedTasksReport


def create_test_tasks():
    """Create a set of test tasks with various tags and patterns."""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    tasks = [
        Task(
            id="1",
            title="Task with multiple tags [FE] [DEL-T] [PDEP]",
            description="Task that should appear in FE, DEL-T, and PDEP categories",
            status=TaskStatus.PENDING,
            priority=Priority.MEDIUM,
            due=today,
            created_at=today,
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="2",
            title="Task with FE and BE tags [FE] [BE]",
            description="Task that should appear in both FE and BE categories",
            status=TaskStatus.PENDING,
            priority=Priority.HIGH,
            due=tomorrow,
            created_at=today - timedelta(days=1),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="3",
            title="Task with only FE tag [FE]",
            description="Task that should appear only in FE category",
            status=TaskStatus.PENDING,
            priority=Priority.MEDIUM,
            due=None,
            created_at=today - timedelta(days=2),
            tags=[],
            tasklist_id="@default"
        ),
    ]
    
    return tasks


def test_multiple_tags():
    """Test that tasks with multiple tags appear in all matching categories."""
    print("Testing Multiple Tags Functionality in Organized Tasks Report (rp9)...")
    
    # Create test tasks
    tasks = create_test_tasks()
    print(f"Created {len(tasks)} test tasks")
    
    # Create report instance
    report = OrganizedTasksReport()
    print(f"Report name: {report.name}")
    
    # Generate report data
    report_data = report.generate(tasks)
    print(f"Generated report with {report_data['total_tasks']} total tasks")
    
    # Check categories
    categories = report_data.get("categories", [])
    print(f"Found {len(categories)} categories with tasks")
    
    # Display the categories and tasks
    for item in categories:
        if isinstance(item, tuple) and len(item) == 2:
            category_key, category_data = item
            tasks_in_category = category_data.get("tasks", [])
            if tasks_in_category:
                print(f"\n{category_key}:")
                for task in tasks_in_category:
                    print(f"  - {task.title}")
    
    # Verify that the task with multiple tags appears in multiple categories
    task_with_multiple_tags_count = 0
    for item in categories:
        if isinstance(item, tuple) and len(item) == 2:
            category_key, category_data = item
            tasks_in_category = category_data.get("tasks", [])
            for task in tasks_in_category:
                if "Task with multiple tags" in task.title:
                    task_with_multiple_tags_count += 1
                    print(f"\nTask with multiple tags found in category: {category_key}")
    
    print(f"\nTask with multiple tags appears in {task_with_multiple_tags_count} categories")
    
    if task_with_multiple_tags_count > 1:
        print("✅ Multiple tags test passed - task appears in multiple categories")
        return True
    else:
        print("❌ Multiple tags test failed - task does not appear in multiple categories")
        return False


if __name__ == "__main__":
    try:
        success = test_multiple_tags()
        if success:
            print("\n✅ All multiple tags tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some multiple tags tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during multiple tags testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)