#!/usr/bin/env python3

import sys
import os
from datetime import datetime, timezone
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.reports.custom_filtered_report import CustomFilteredReport

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli/src'))

def test_datetime_comparison():
    """Test the datetime comparison issue."""
    print("Testing datetime comparison issue...")
    
    # Create sample tasks with different datetime formats
    now = datetime.now()
    utc_now = datetime.now(timezone.utc)
    
    task1 = Task(
        id="1",
        title="Test task 1",
        tasklist_id="list1",
        created_at=now,  # Naive datetime
        modified_at=now.replace(tzinfo=None)  # Also naive
    )
    
    task2 = Task(
        id="2",
        title="Test task 2",
        tasklist_id="list1",
        created_at=utc_now,  # Aware datetime
        modified_at=utc_now  # Also aware
    )
    
    tasks = [task1, task2]
    report = CustomFilteredReport()
    
    # Try to apply a date filter - this should trigger the error
    try:
        filtered = report._apply_date_filter(tasks, "this_week:created_at")
        print(f"Successfully filtered tasks. Result: {len(filtered)} tasks")
        for task in filtered:
            print(f"  Task {task.id}: {task.title}")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_datetime_comparison()