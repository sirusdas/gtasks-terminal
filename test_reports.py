#!/usr/bin/env python3
"""
Test script to verify that the reports module works correctly.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.reports.base_report import ReportManager
from gtasks_cli.reports.task_completion_report import TaskCompletionReport
from gtasks_cli.reports.pending_tasks_report import PendingTasksReport
from gtasks_cli.reports.overdue_tasks_report import OverdueTasksReport


def test_reports():
    """Test that the reports module works correctly."""
    print("🔍 Testing reports module...")
    
    # Create some test tasks
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    last_week = today - timedelta(days=7)
    next_week = today + timedelta(days=7)
    
    tasks = [
        Task(
            id=str(uuid.uuid4()),
            title="Completed Task 1",
            description="This task is completed",
            status=TaskStatus.COMPLETED,
            priority=Priority.HIGH,
            due=yesterday,
            created_at=last_week,
            completed_at=yesterday,
            tags=["work", "urgent"],
            tasklist_id="@default"
        ),
        Task(
            id=str(uuid.uuid4()),
            title="Pending Task 1",
            description="This task is pending",
            status=TaskStatus.PENDING,
            priority=Priority.MEDIUM,
            due=tomorrow,
            created_at=yesterday,
            tags=["personal"],
            tasklist_id="@default"
        ),
        Task(
            id=str(uuid.uuid4()),
            title="Overdue Task 1",
            description="This task is overdue",
            status=TaskStatus.PENDING,
            priority=Priority.HIGH,
            due=last_week,
            created_at=last_week - timedelta(days=10),
            tags=["work", "overdue"],
            tasklist_id="@default"
        ),
        Task(
            id=str(uuid.uuid4()),
            title="Future Task 1",
            description="This task is for the future",
            status=TaskStatus.PENDING,
            priority=Priority.LOW,
            due=next_week,
            created_at=today,
            tags=["personal", "planning"],
            tasklist_id="@default"
        ),
        Task(
            id=str(uuid.uuid4()),
            title="No Due Date Task",
            description="This task has no due date",
            status=TaskStatus.PENDING,
            priority=Priority.MEDIUM,
            due=None,
            created_at=yesterday,
            tags=[],
            tasklist_id="@default"
        )
    ]
    
    print(f"✅ Created {len(tasks)} test tasks")
    
    # Test TaskCompletionReport
    print("\n1. Testing TaskCompletionReport...")
    completion_report = TaskCompletionReport()
    completion_data = completion_report.generate(tasks, period_days=30)
    completion_text = completion_report.export(completion_data, 'txt')
    print("   ✅ TaskCompletionReport generated successfully")
    print(f"   📊 Total completed tasks: {completion_data['total_completed']}")
    
    # Test PendingTasksReport
    print("\n2. Testing PendingTasksReport...")
    pending_report = PendingTasksReport()
    pending_data = pending_report.generate(tasks)
    pending_text = pending_report.export(pending_data, 'txt')
    print("   ✅ PendingTasksReport generated successfully")
    print(f"   📊 Total pending tasks: {pending_data['total_pending']}")
    
    # Test OverdueTasksReport
    print("\n3. Testing OverdueTasksReport...")
    overdue_report = OverdueTasksReport()
    overdue_data = overdue_report.generate(tasks)
    overdue_text = overdue_report.export(overdue_data, 'txt')
    print("   ✅ OverdueTasksReport generated successfully")
    print(f"   📊 Total overdue tasks: {overdue_data['total_overdue']}")
    
    # Test ReportManager
    print("\n4. Testing ReportManager...")
    report_manager = ReportManager()
    report_manager.register_report('rp1', completion_report)
    report_manager.register_report('rp2', pending_report)
    report_manager.register_report('rp4', overdue_report)
    
    reports_list = report_manager.list_reports()
    print("   ✅ ReportManager works correctly")
    print(f"   📋 Available reports: {len(reports_list)}")
    
    # Test generating reports through ReportManager
    completion_data_via_manager = report_manager.generate_report('rp1', tasks, period_days=30)
    if completion_data_via_manager:
        print("   ✅ Report generation via ReportManager successful")
    
    # Test exporting reports through ReportManager
    exported_text = report_manager.export_report('rp1', completion_data_via_manager, 'txt')
    if exported_text:
        print("   ✅ Report export via ReportManager successful")
    
    print("\n🎉 All reports tests completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = test_reports()
        if success:
            print("\n✅ All reports tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some reports tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during reports testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)