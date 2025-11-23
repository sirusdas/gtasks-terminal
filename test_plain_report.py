#!/usr/bin/env python3
"""
Test script for the plain text output of the Organized Tasks Report (rp9)
"""

import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))


def create_test_tasks():
    """Create a set of test tasks with various tags and patterns."""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    from gtasks_cli.models.task import Task, TaskStatus, Priority
    
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


def test_plain_report():
    """Test the plain text output of the organized tasks report."""
    print("Testing Plain Text Output of Organized Tasks Report (rp9)...")
    
    # Create test tasks
    tasks = create_test_tasks()
    print(f"Created {len(tasks)} test tasks")
    
    # Temporarily hide the rich module to test plain text
    import sys
    original_modules = dict(sys.modules)
    
    # Hide rich modules
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('rich'):
            del sys.modules[module_name]
    
    # Reimport the report module to force plain text mode
    if 'gtasks_cli.reports.organized_tasks_report' in sys.modules:
        del sys.modules['gtasks_cli.reports.organized_tasks_report']
    
    # Reimport to get the plain text version
    from gtasks_cli.reports.organized_tasks_report import OrganizedTasksReport
    report = OrganizedTasksReport()
    
    print(f"Report name: {report.name}")
    
    # Generate report data
    report_data = report.generate(tasks)
    print(f"Generated report with {report_data['total_tasks']} total tasks")
    
    # Export to text format
    text_export = report.export(report_data, 'txt')
    print("\nPlain Text Export:")
    print("=" * 50)
    print(text_export)
    
    # Restore original modules
    sys.modules.update(original_modules)
    
    print("\n✅ Plain text test completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = test_plain_report()
        if success:
            print("\n✅ All plain text tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some plain text tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during plain text testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)