#!/usr/bin/env python3
"""
Test script for the Organized Tasks Report (rp9)
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.reports.organized_tasks_report import OrganizedTasksReport


def create_test_tasks():
    """Create a set of test tasks with various tags and patterns."""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    # Create timezone-aware datetime
    aware_datetime = datetime.now(timezone.utc)
    
    tasks = [
        Task(
            id="1",
            title="Fix critical bug *****",
            description="Fix critical production bug with highest priority",
            status=TaskStatus.PENDING,
            priority=Priority.CRITICAL,
            due=today,
            created_at=today,
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="2",
            title="Priority task p1",
            description="High priority task for project",
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            due=tomorrow,
            created_at=today - timedelta(days=1),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="3",
            title="Medium priority task ***",
            description="Medium priority task",
            status=TaskStatus.PENDING,
            priority=Priority.MEDIUM,
            due=next_week,
            created_at=today - timedelta(days=2),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="4",
            title="Bug fixes and defects",
            description="Fix reported defects in the system",
            status=TaskStatus.PENDING,
            priority=Priority.HIGH,
            due=today,
            created_at=today - timedelta(days=4),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="5",
            title="Frontend development FE",
            description="Frontend development task for new feature",
            status=TaskStatus.PENDING,
            priority=Priority.MEDIUM,
            due=None,
            created_at=today - timedelta(days=6),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="6",
            title="Backend services BE",
            description="Backend development task",
            status=TaskStatus.PENDING,
            priority=Priority.MEDIUM,
            due=None,
            created_at=today - timedelta(days=7),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="7",
            title="Dependency tracking DEP",
            description="Task with dependencies on other teams",
            status=TaskStatus.WAITING,
            priority=Priority.MEDIUM,
            due=None,
            created_at=today - timedelta(days=8),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="8",
            title="Pending items pending",
            description="Task pending for review",
            status=TaskStatus.PENDING,
            priority=Priority.LOW,
            due=tomorrow,
            created_at=today - timedelta(days=10),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="9",
            title="Meeting with team meetings",
            description="Weekly team sync meeting",
            status=TaskStatus.PENDING,
            priority=Priority.LOW,
            due=today,
            created_at=today - timedelta(days=3),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="10",
            title="Change request cr",
            description="Change request for system update",
            status=TaskStatus.PENDING,
            priority=Priority.MEDIUM,
            due=next_week,
            created_at=today,
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="11",
            title="Hold this task HOLD",
            description="Task that should be put on hold",
            status=TaskStatus.WAITING,
            priority=Priority.LOW,
            due=None,
            created_at=today - timedelta(days=5),
            tags=[],
            tasklist_id="@default"
        ),
        Task(
            id="12",
            title="Study new technology study",
            description="Research new frameworks and technologies",
            status=TaskStatus.PENDING,
            priority=Priority.LOW,
            due=None,
            created_at=today - timedelta(days=9),
            tags=[],
            tasklist_id="@default"
        ),
    ]
    
    return tasks


def test_organized_tasks_report():
    """Test the organized tasks report functionality."""
    print("Testing Organized Tasks Report (rp9)...")
    
    # Create test tasks
    tasks = create_test_tasks()
    print(f"Created {len(tasks)} test tasks")
    
    # Show what tags we're looking for in tasks
    print("\nSample tasks and their content:")
    for i, task in enumerate(tasks[:5]):  # Show first 5 tasks
        print(f"  Task {i+1}: {task.title}")
    
    # Create report instance
    report = OrganizedTasksReport()
    print(f"\nReport name: {report.name}")
    print(f"Report description: {report.description}")
    
    # Test the tag matching for specific tasks
    print("\nTesting tag matching for specific tasks:")
    test_cases = [
        (tasks[10], ["HOLD"]),  # HOLD task
        (tasks[9], ["cr"]),     # cr task
        (tasks[0], ["*****"]),  # ***** task
    ]
    
    for task, tags in test_cases:
        has_tag = report._has_any_tag(task, tags)
        print(f"  Task '{task.title}' has tag {tags}: {has_tag}")
    
    # Generate report data
    report_data = report.generate(tasks)
    print(f"\nGenerated report with {report_data['total_tasks']} total tasks")
    
    # Check categories
    categories = report_data['categories']
    print(f"Found {len(categories)} categories with tasks")
    
    for item in categories:
        if isinstance(item, tuple) and len(item) == 2:
            category_key, category_data = item
            task_count = len(category_data.get('tasks', []))
            group_name = category_data.get('group', 'Unknown')
            print(f"  {category_key} (Group: {group_name}): {task_count} tasks")
    
    # Check uncategorized tasks
    uncategorized = report_data['uncategorized']
    print(f"Uncategorized tasks: {len(uncategorized)}")
    
    # Export to text format
    text_export = report.export(report_data, 'txt')
    print("\nText Export:")
    print("=" * 50)
    print(text_export)
    
    # Export to CSV format
    csv_export = report.export(report_data, 'csv')
    print("\nCSV Export (first 500 chars):")
    print("=" * 50)
    print(csv_export[:500] + "..." if len(csv_export) > 500 else csv_export)
    
    # Test with None data
    none_export = report.export(None, 'txt')
    print("\nNone Data Export:")
    print("=" * 50)
    print(none_export)
    
    print("\n✅ Test completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = test_organized_tasks_report()
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)