#!/usr/bin/env python3
"""
Task Completion Report - Summary of completed tasks over a specified period.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.reports.base_report import BaseReport
from gtasks_cli.utils.logger import setup_logger
import csv
import io

logger = setup_logger(__name__)


class TaskCompletionReport(BaseReport):
    """Report showing summary of completed tasks over a specified period."""
    
    def __init__(self):
        """Initialize the task completion report."""
        super().__init__(
            name="Task Completion Report",
            description="Summary of completed tasks over a specified period"
        )
    
    def generate(self, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """
        Generate the task completion report.
        
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
        
        # Make sure all dates are timezone-naive for comparison
        if hasattr(start_date, 'tzinfo') and start_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=None)
        if hasattr(end_date, 'tzinfo') and end_date.tzinfo is not None:
            end_date = end_date.replace(tzinfo=None)
        
        # Set end_date to end of day if it was just date (00:00:00)
        if end_date.hour == 0 and end_date.minute == 0 and end_date.second == 0:
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Filter completed tasks within the date range
        completed_tasks = []
        for task in tasks:
            if task.status == TaskStatus.COMPLETED and task.completed_at:
                # Make sure task.completed_at is timezone-naive for comparison
                task_completed_at = task.completed_at
                if hasattr(task_completed_at, 'tzinfo') and task_completed_at.tzinfo is not None:
                    task_completed_at = task_completed_at.replace(tzinfo=None)
                
                if start_date <= task_completed_at <= end_date:
                    completed_tasks.append(task)
        
        # Group by date
        daily_completion = {}
        for task in completed_tasks:
            # Make sure task.completed_at is timezone-naive for date extraction
            task_completed_at = task.completed_at
            if hasattr(task_completed_at, 'tzinfo') and task_completed_at.tzinfo is not None:
                task_completed_at = task_completed_at.replace(tzinfo=None)
            
            date_key = task_completed_at.date().isoformat()
            if date_key not in daily_completion:
                daily_completion[date_key] = []
            daily_completion[date_key].append(task)
        
        # Calculate statistics
        total_completed = len(completed_tasks)
        daily_counts = {date: len(tasks) for date, tasks in daily_completion.items()}
        average_per_day = total_completed / period_days if period_days > 0 else 0
        
        report_data = {
            'report_name': self.name,
            'report_description': self.description,
            'period_start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
            'period_end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
            'period_days': period_days,
            'total_completed': total_completed,
            'completed_tasks': completed_tasks,
            'tasks': completed_tasks,
            'daily_completion': daily_completion,
            'daily_counts': daily_counts,
            'average_per_day': average_per_day,
            'completion_rate': (total_completed / len(tasks) * 100) if tasks else 0
        }
        
        logger.debug(f"Generated task completion report with {total_completed} completed tasks")
        return report_data
    
    def export(self, data: Dict[str, Any], format: str = 'txt') -> str:
        """
        Export the task completion report in the specified format.
        
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
        output.append(f"")
        output.append(f"Summary:")
        output.append(f"  Total completed tasks: {data['total_completed']}")
        output.append(f"  Average per day: {data['average_per_day']:.2f}")
        output.append(f"  Completion rate: {data['completion_rate']:.2f}%")
        output.append(f"")
        output.append(f"Daily Completion:")
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
        writer.writerow([])  # Empty row
        
        # Summary
        writer.writerow(['Summary'])
        writer.writerow(['Total Completed Tasks', data['total_completed']])
        writer.writerow(['Average Per Day', f"{data['average_per_day']:.2f}"])
        writer.writerow(['Completion Rate %', f"{data['completion_rate']:.2f}"])
        writer.writerow([])  # Empty row
        
        # Daily completion
        writer.writerow(['Daily Completion'])
        writer.writerow(['Date', 'Count'])
        for date, count in sorted(data['daily_counts'].items()):
            writer.writerow([date, count])
        
        return output.getvalue()