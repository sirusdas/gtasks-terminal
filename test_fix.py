#!/usr/bin/env python3

import sys
import os
from datetime import datetime
from gtasks_cli.storage.sqlite_storage import SQLiteStorage
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.reports.custom_filtered_report import CustomFilteredReport

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli/src'))

def test_custom_filtered_report():
    """Test the CustomFilteredReport with the fixed timezone handling."""
    print("Testing CustomFilteredReport with timezone fix...")
    
    # Initialize task manager to get tasks (similar to how generate_report does)
    task_manager = TaskManager(
        use_google_tasks=False,
        storage_backend='sqlite',
        account_name='work'
    )
    
    # Load tasks
    try:
        tasks = task_manager.list_tasks()
        print(f"Loaded {len(tasks)} tasks for testing")
    except Exception as e:
        print(f"Error loading tasks: {e}")
        return
    
    # Filter tasks by pending status (like --only-pending does)
    from gtasks_cli.models.task import TaskStatus
    pending_tasks = [task for task in tasks if task.status == TaskStatus.PENDING]
    print(f"Filtered to {len(pending_tasks)} pending tasks")
    
    # Test the report with the problematic filter
    report = CustomFilteredReport()
    
    try:
        print("\nTesting with filter 'this_week:created_at'...")
        filtered = report._apply_date_filter(pending_tasks, "this_week:created_at")
        print(f"Successfully filtered tasks. Result: {len(filtered)} tasks")
        
        # Test with tags filter as well
        print("\nTesting with tags filter 'my'...")
        tagged = report._apply_tags_filter(filtered, "my")
        print(f"After applying tags filter: {len(tagged)} tasks")
        
        # Test full report generation
        print("\nTesting full report generation...")
        report_data = report.generate(
            tagged, 
            filter_str="this_week:created_at",
            tags_filter="my",
            order_by="modified_at:desc",
            output_tags="--ex:tp1,R,PH|--group:1[my,***,urgent],2[prod]",
            output_lists="--ex:Raju Da",
            output_tasks="--ex:Tracker"
        )
        print(f"Report generated successfully with {report_data['total_tasks']} tasks")
        print(f"Title: {report_data['title']}")
        
        # Test export
        exported = report.export(report_data, format='txt', color=False)
        print("Report exported successfully")
        print(f"Export preview (first 500 chars):\n{exported[:500]}...")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_custom_filtered_report()