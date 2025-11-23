#!/usr/bin/env python3
"""
Timeline Report - A visual representation of tasks completed over a specified time period.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.reports.base_report import BaseReport
from gtasks_cli.utils.logger import setup_logger
import csv
import io

logger = setup_logger(__name__)


class TimelineReport(BaseReport):
    """Report showing a visual representation of tasks completed over a specified time period."""
    
    def __init__(self):
        """Initialize the timeline report."""
        super().__init__(
            name="Timeline Report",
            description="A visual representation of tasks completed over a specified time period"
        )
    
    def generate(self, tasks: List[Task], **kwargs) -> Dict[str, Any]:
        """
        Generate the timeline report.
        
        Args:
            tasks: List of tasks to generate report from
            **kwargs: Additional parameters (start_date, end_date, period_days)
            
        Returns:
            Dict containing report data
        """
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        period_days = kwargs.get('period_days', 30)
        
        # If no dates provided, use last N days
        if not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
        elif not end_date:
            end_date = datetime.now()
        elif not start_date:
            start_date = end_date - timedelta(days=period_days)

        # Make sure all dates are timezone-naive for comparison
        if hasattr(start_date, 'tzinfo') and start_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=None)
        if hasattr(end_date, 'tzinfo') and end_date.tzinfo is not None:
            end_date = end_date.replace(tzinfo=None)
        
        # Filter tasks within the date range (created or completed)
        relevant_tasks = []
        for task in tasks:
            added = False  # Track if task was already added

            if task.created_at:
                # Make sure created_at is timezone-naive for comparison
                created_at = task.created_at
                if hasattr(created_at, 'tzinfo') and created_at.tzinfo is not None:
                    created_at = created_at.replace(tzinfo=None)

                if start_date <= created_at <= end_date:
                    relevant_tasks.append(task)
                    added = True

            if task.completed_at:
                # Make sure completed_at is timezone-naive for comparison
                completed_at = task.completed_at
                if hasattr(completed_at, 'tzinfo') and completed_at.tzinfo is not None:
                    completed_at = completed_at.replace(tzinfo=None)

                if start_date <= completed_at <= end_date:
                    # Avoid duplicates
                    if not added:
                        relevant_tasks.append(task)
        
        # Group by date for visualization
        created_by_date = {}
        completed_by_date = {}
        
        current_date = start_date.date()
        end_date_obj = end_date.date()
        
        # Initialize all dates in range
        while current_date <= end_date_obj:
            created_by_date[current_date.isoformat()] = []
            completed_by_date[current_date.isoformat()] = []
            current_date += timedelta(days=1)
        
        # Populate with actual data
        for task in relevant_tasks:
            if task.created_at:
                created_date = task.created_at.date().isoformat()
                if created_date in created_by_date:
                    created_by_date[created_date].append(task)
            
            if task.completed_at:
                completed_date = task.completed_at.date().isoformat()
                if completed_date in completed_by_date:
                    completed_by_date[completed_date].append(task)
        
        # Calculate daily statistics
        daily_stats = {}
        for date_str in created_by_date.keys():
            daily_stats[date_str] = {
                'created': len(created_by_date[date_str]),
                'completed': len(completed_by_date[date_str])
            }
        
        # Find max values for scaling
        max_created = max(stats['created'] for stats in daily_stats.values()) if daily_stats else 1
        max_completed = max(stats['completed'] for stats in daily_stats.values()) if daily_stats else 1
        max_combined = max(max_created, max_completed)
        
        report_data = {
            'report_name': self.name,
            'report_description': self.description,
            'period_start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
            'period_end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
            'period_days': period_days,
            'total_relevant_tasks': len(relevant_tasks),
            'created_by_date': created_by_date,
            'completed_by_date': completed_by_date,
            'daily_stats': daily_stats,
            'max_created': max_created,
            'max_completed': max_completed,
            'max_combined': max_combined,
            'generated_at': datetime.now().isoformat()
        }
        
        logger.debug(f"Generated timeline report for {len(relevant_tasks)} relevant tasks")
        return report_data
    
    def export(self, data: Dict[str, Any], format: str = 'txt') -> str:
        """
        Export the timeline report in the specified format.
        
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
        """Export report as text with ASCII timeline visualization."""
        output = []
        output.append("=" * 60)
        output.append(f"{data['report_name']}")
        output.append("=" * 60)
        output.append(f"Description: {data['report_description']}")
        output.append(f"Period: {data['period_start']} to {data['period_end']} ({data['period_days']} days)")
        output.append(f"Generated at: {data['generated_at']}")
        output.append(f"")
        output.append(f"Summary:")
        output.append(f"  Total relevant tasks: {data['total_relevant_tasks']}")
        output.append(f"  Max tasks created in a day: {data['max_created']}")
        output.append(f"  Max tasks completed in a day: {data['max_completed']}")
        output.append(f"")
        
        # ASCII timeline visualization
        output.append("Timeline Visualization:")
        output.append("(C: Created tasks, ⬤: Completed tasks)")
        output.append("")
        
        # Create a simple bar chart representation
        chart_width = 50
        for date_str, stats in sorted(data['daily_stats'].items()):
            # Skip dates with no activity for brevity
            if stats['created'] == 0 and stats['completed'] == 0:
                continue
                
            date_display = date_str.split('T')[0]  # Just the date part
            created_bar = '█' * int((stats['created'] / data['max_combined']) * chart_width) if data['max_combined'] > 0 else ''
            completed_bar = '●' * int((stats['completed'] / data['max_combined']) * chart_width) if data['max_combined'] > 0 else ''
            
            output.append(f"{date_display:10} | C:{created_bar:<{chart_width}} | ⬤:{completed_bar:<{chart_width}} | "
                         f"({stats['created']} created, {stats['completed']} completed)")
        
        output.append("")
        output.append("Legend:")
        output.append("  C: Created tasks")
        output.append("  ⬤: Completed tasks")
        
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
        writer.writerow(['Max Created in a Day', data['max_created']])
        writer.writerow(['Max Completed in a Day', data['max_completed']])
        writer.writerow([])  # Empty row
        
        # Daily statistics
        writer.writerow(['Daily Statistics'])
        writer.writerow(['Date', 'Created Tasks', 'Completed Tasks'])
        for date_str, stats in sorted(data['daily_stats'].items()):
            writer.writerow([date_str, stats['created'], stats['completed']])
        
        return output.getvalue()