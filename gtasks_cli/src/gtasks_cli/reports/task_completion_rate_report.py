#!/usr/bin/env python3
"""
Task Completion Rate Report - Percentage of tasks completed over a given period.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.reports.base_report import BaseReport
from gtasks_cli.utils.logger import setup_logger
import csv
import io

logger = setup_logger(__name__)


class TaskCompletionRateReport(BaseReport):
    """Report showing percentage of tasks completed over a given period."""
    
    def __init__(self):
        """Initialize the task completion rate report."""
        super().__init__(
            name="Task Completion Rate Report",
            description="Percentage of tasks completed over a given period"
        )
    
    def generate(self, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """
        Generate the task completion rate report.
        
        Args:
            tasks: List of tasks to generate report from
            **kwargs: Additional parameters (start_date, end_date, period_days)
            
        Returns:
            Dict containing report data
        """
        def _make_naive(dt: Optional[datetime]) -> Optional[datetime]:
            """Convert timezone-aware datetime to timezone-naive for comparison."""
            if dt and hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt

        start_date = _make_naive(kwargs.get('start_date'))
        end_date = _make_naive(kwargs.get('end_date'))
        period_days = kwargs.get('period_days', 30)
        
        # If no dates provided, use last N days
        if not start_date and not end_date:
            now = _make_naive(datetime.now())
            end_date = now
            start_date = now - timedelta(days=period_days)
        elif not end_date:
            end_date = _make_naive(datetime.now())
        elif not start_date:
            start_date = end_date - timedelta(days=period_days)
        
        # Filter tasks within the date range (created or completed)
        relevant_tasks = []
        for task in tasks:
            created_at = _make_naive(task.created_at)
            completed_at = _make_naive(task.completed_at)
            
            # Check if task was created within the date range
            created_in_range = False
            if created_at is not None and start_date is not None and end_date is not None:
                created_in_range = start_date <= created_at <= end_date
            
            # Check if task was completed within the date range
            completed_in_range = False
            if completed_at is not None and start_date is not None and end_date is not None:
                completed_in_range = start_date <= completed_at <= end_date
            
            if created_in_range or completed_in_range:
                relevant_tasks.append(task)
        
        # Calculate completion rate
        total_relevant = len(relevant_tasks)
        completed_tasks = [task for task in relevant_tasks if task.status == TaskStatus.COMPLETED]
        total_completed = len(completed_tasks)
        
        completion_rate = (total_completed / total_relevant * 100) if total_relevant > 0 else 0
        
        # Weekly breakdown if period is long enough
        weekly_data = {}
        if period_days >= 7:
            weeks = period_days // 7
            for i in range(weeks):
                week_start = start_date + timedelta(days=i*7)
                week_end = start_date + timedelta(days=(i+1)*7)
                
                week_tasks = []
                for task in relevant_tasks:
                    created_at = _make_naive(task.created_at)
                    completed_at = _make_naive(task.completed_at)
                    
                    # Check if task was created within the week
                    created_in_week = False
                    if created_at is not None and week_start is not None and week_end is not None:
                        created_in_week = week_start <= created_at <= week_end
                    
                    # Check if task was completed within the week
                    completed_in_week = False
                    if completed_at is not None and week_start is not None and week_end is not None:
                        completed_in_week = week_start <= completed_at <= week_end
                    
                    if created_in_week or completed_in_week:
                        # Avoid duplicates
                        if task not in week_tasks:
                            week_tasks.append(task)
                
                week_completed = [task for task in week_tasks if task.status == TaskStatus.COMPLETED]
                
                weekly_completion_rate = (len(week_completed) / len(week_tasks) * 100) if week_tasks else 0
                
                week_key = f"Week {i+1} ({week_start.strftime('%m/%d')}-{week_end.strftime('%m/%d')})"
                weekly_data[week_key] = {
                    'total': len(week_tasks),
                    'completed': len(week_completed),
                    'completion_rate': weekly_completion_rate
                }
        
        report_data = {
            'report_name': self.name,
            'report_description': self.description,
            'period_start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
            'period_end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
            'period_days': period_days,
            'total_relevant_tasks': total_relevant,
            'total_completed_tasks': total_completed,
            'completion_rate': completion_rate,
            'weekly_data': weekly_data,
            'generated_at': datetime.now().isoformat()
        }
        
        logger.debug(f"Generated task completion rate report: {completion_rate:.1f}% completion rate")
        return report_data
    
    def export(self, data: Dict[str, Any], format: str = 'txt') -> str:
        """
        Export the task completion rate report in the specified format.
        
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
        output.append(f"  Total relevant tasks: {data['total_relevant_tasks']}")
        output.append(f"  Completed tasks: {data['total_completed_tasks']}")
        output.append(f"  Completion rate: {data['completion_rate']:.1f}%")
        output.append(f"")
        
        if data['weekly_data']:
            output.append(f"Weekly Completion Rates:")
            for week, stats in data['weekly_data'].items():
                output.append(f"  {week}: {stats['completed']}/{stats['total']} tasks completed ({stats['completion_rate']:.1f}%)")
        
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
        writer.writerow(['Total Relevant Tasks', data['total_relevant_tasks']])
        writer.writerow(['Completed Tasks', data['total_completed_tasks']])
        writer.writerow(['Completion Rate %', f"{data['completion_rate']:.1f}"])
        writer.writerow([])  # Empty row
        
        # Weekly data
        if data['weekly_data']:
            writer.writerow(['Weekly Data'])
            writer.writerow(['Week', 'Total Tasks', 'Completed Tasks', 'Completion Rate %'])
            for week, stats in data['weekly_data'].items():
                writer.writerow([week, stats['total'], stats['completed'], f"{stats['completion_rate']:.1f}"])
        
        return output.getvalue()