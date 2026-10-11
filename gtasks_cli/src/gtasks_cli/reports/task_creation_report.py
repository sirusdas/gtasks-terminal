#!/usr/bin/env python3
"""
Task Creation Report - Overview of tasks created within a certain timeframe.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.reports.base_report import BaseReport
from gtasks_cli.utils.logger import setup_logger
import csv
import io

logger = setup_logger(__name__)


class TaskCreationReport(BaseReport):
    """Report showing overview of tasks created within a certain timeframe."""
    
    def __init__(self):
        """Initialize the task creation report."""
        super().__init__(
            name="Task Creation Report",
            description="Overview of tasks created within a certain timeframe"
        )
    
    def generate(self, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """
        Generate the task creation report.
        
        Args:
            tasks: List of tasks to generate report from
            **kwargs: Additional parameters (start_date, end_date, period_days)
            
        Returns:
            Dict containing report data
        """
        def _parse_dt(d):
            if isinstance(d, str):
                try:
                    return datetime.fromisoformat(d.replace('Z', '+00:00'))
                except Exception:
                    pass
            return d

        start_date = _parse_dt(kwargs.get('start_date'))
        end_date = _parse_dt(kwargs.get('end_date'))
        period_days = kwargs.get('period_days')
        if period_days is None:
            if start_date and end_date:
                period_days = max(1, (end_date - start_date).days)
            else:
                period_days = 30
        else:
            try:
                period_days = int(period_days)
            except Exception:
                period_days = 30
        
        # If no dates provided, use last N days
        now = datetime.now()
        if not start_date and not end_date:
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            start_date = (now - timedelta(days=period_days)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif not end_date:
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif not start_date:
            start_date = (end_date - timedelta(days=period_days)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Ensure timezone-naive comparison
        if hasattr(start_date, 'tzinfo') and start_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=None)
        if hasattr(end_date, 'tzinfo') and end_date.tzinfo is not None:
            end_date = end_date.replace(tzinfo=None)
        
        if end_date.hour == 0 and end_date.minute == 0 and end_date.second == 0:
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Filter tasks created within the date range
        created_tasks = []
        for task in tasks:
            if task.created_at:
                task_created = task.created_at
                if hasattr(task_created, 'tzinfo') and task_created.tzinfo is not None:
                    task_created = task_created.replace(tzinfo=None)
                if start_date <= task_created <= end_date:
                    created_tasks.append(task)
        
        # Group by date
        daily_creation = {}
        for task in created_tasks:
            date_key = task.created_at.date().isoformat()
            if date_key not in daily_creation:
                daily_creation[date_key] = []
            daily_creation[date_key].append(task)
        
        # Calculate statistics
        total_created = len(created_tasks)
        daily_counts = {date: len(tasks) for date, tasks in daily_creation.items()}
        average_per_day = total_created / period_days if period_days > 0 else 0
        
        # Categorize by status
        pending_tasks = [task for task in created_tasks if task.status == TaskStatus.PENDING]
        completed_tasks = [task for task in created_tasks if task.status == TaskStatus.COMPLETED]
        in_progress_tasks = [task for task in created_tasks if task.status == TaskStatus.IN_PROGRESS]
        waiting_tasks = [task for task in created_tasks if task.status == TaskStatus.WAITING]
        
        report_data = {
            'report_name': self.name,
            'report_description': self.description,
            'period_start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
            'period_end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
            'period_days': period_days,
            'total_created': total_created,
            'created_tasks': created_tasks,
            'tasks': created_tasks,
            'daily_creation': daily_creation,
            'daily_counts': daily_counts,
            'average_per_day': average_per_day,
            'pending': pending_tasks,
            'completed': completed_tasks,
            'in_progress': in_progress_tasks,
            'waiting': waiting_tasks,
            'generated_at': datetime.now().isoformat()
        }
        
        logger.debug(f"Generated task creation report with {total_created} created tasks")
        return report_data
    
    def export(self, data: Dict[str, Any], format: str = 'txt') -> str:
        """
        Export the task creation report in the specified format.
        
        Args:
            data: Report data generated by generate() method
            format: Export format (txt, csv)
            
        Returns:
            String representation of the exported report
        """
        if format.lower() == 'csv':
            return self._export_csv(data)
        else:
            return self._export_text(data)
    
    def _export_text(self, data: Dict[str, Any]) -> str:
        """Export report as text."""
        output = []
        output.append("=" * 50)
        output.append(f"{data['report_name']}")
        output.append("=" * 50)
        output.append(f"Description: {data['report_description']}")
        output.append(f"Period: {data['period_start']} to {data['period_end']} ({data['period_days']} days)")
        output.append(f"Generated at: {data['generated_at']}")
        output.append(f"")
        output.append(f"Summary:")
        output.append(f"  Total created tasks: {data['total_created']}")
        output.append(f"  Average per day: {data['average_per_day']:.2f}")
        output.append(f"  Pending: {len(data['pending'])}")
        output.append(f"  Completed: {len(data['completed'])}")
        output.append(f"  In Progress: {len(data['in_progress'])}")
        output.append(f"  Waiting: {len(data['waiting'])}")
        output.append(f"")
        output.append(f"Daily Creation:")
        for date, count in sorted(data['daily_counts'].items()):
            output.append(f"  {date}: {count} tasks")
        
        return "\n".join(output)
    
    def _export_csv(self, data: Dict[str, Any]) -> str:
        """Export report as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Report', data['report_name']])
        writer.writerow(['Description', data['report_description']])
        writer.writerow(['Period Start', data['period_start']])
        writer.writerow(['Period End', data['period_end']])
        writer.writerow(['Period Days', data['period_days']])
        writer.writerow(['Generated At', data['generated_at']])
        writer.writerow([])  # Empty row
        
        # Summary
        writer.writerow(['Summary'])
        writer.writerow(['Total Created Tasks', data['total_created']])
        writer.writerow(['Average Per Day', f"{data['average_per_day']:.2f}"])
        writer.writerow(['Pending', len(data['pending'])])
        writer.writerow(['Completed', len(data['completed'])])
        writer.writerow(['In Progress', len(data['in_progress'])])
        writer.writerow(['Waiting', len(data['waiting'])])
        writer.writerow([])  # Empty row
        
        # Daily creation
        writer.writerow(['Daily Creation'])
        writer.writerow(['Date', 'Count'])
        for date, count in sorted(data['daily_counts'].items()):
            writer.writerow([date, count])
        
        return output.getvalue()