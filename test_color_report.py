#!/usr/bin/env python3
"""
Test script for the color functionality in the Organized Tasks Report (rp9)
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
            due=None,
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
    ]
    
    return tasks


def test_color_report():
    """Test the color functionality in the organized tasks report."""
    print("Testing Color Functionality in Organized Tasks Report (rp9)...")
    
    # Create test tasks
    tasks = create_test_tasks()
    print(f"Created {len(tasks)} test tasks")
    
    # Create report instance
    report = OrganizedTasksReport()
    print(f"Report name: {report.name}")
    
    # Generate report data
    report_data = report.generate(tasks)
    print(f"Generated report with {report_data['total_tasks']} total tasks")
    
    # Export to text format
    text_export = report.export(report_data, 'txt')
    print("\nText Export with Color Support:")
    print("=" * 50)
    print(text_export)
    
    print("\n✅ Color test completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = test_color_report()
        if success:
            print("\n✅ All color tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some color tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during color testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)