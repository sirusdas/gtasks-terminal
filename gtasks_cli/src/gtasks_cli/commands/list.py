from typing import List
from gtasks_cli.models.task import Task
from gtasks_cli.models.task_list import TaskList
from datetime import datetime, timedelta  # Needed for date formatting
from gtasks_cli.utils.datetime_utils import _normalize_datetime
import click


def display_tasks_grouped_by_list(tasks: List[Task]):
    """Display tasks grouped by their task lists with color coding."""
    if not tasks:
        click.echo("No tasks found.")
        return
    
    # Group tasks by list
    tasks_by_list = {}
    for task in tasks:
        list_id = getattr(task, 'tasklist_id', 'default')  # Handle both Google and local tasks
        if list_id not in tasks_by_list:
            tasks_by_list[list_id] = {
                'title': getattr(task, 'list_title', 'Untitled List'),
                'tasks': []
            }
        tasks_by_list[list_id]['tasks'].append(task)
    
    # Display tasks grouped by list
    for list_info in tasks_by_list.values():
        list_title = list_info['title']
        tasks = list_info['tasks']
        
        # Use different colors for different lists
        list_title_color = _get_list_color(list_title)
        click.secho(f"\n{list_title}", fg=list_title_color, bold=True)
        
        for i, task in enumerate(tasks, 1):
            # Format the task line with priority indicator
            priority_icon = _get_priority_icon(task.priority)
            
            # Format due date
            due_str = _format_due_date(task.due)
            
            # Build the task line
            task_line = f"{i:2d}. {priority_icon} {task.title}{due_str}"
            
            # Color code task status
            task_color = _get_status_color(task.status)
            click.secho(task_line, fg=task_color)
            
            # Display description if available
            if task.description:
                click.echo(f"     📝 {task.description[:60]}{'...' if len(task.description) > 60 else ''}")
    
    # Summary
    click.echo(f"\nTotal: {len(tasks)} task(s) across {len(tasks_by_list)} list(s)")

def _get_list_color(list_title: str) -> str:
    """Get color for list title based on its name"""
    # Use a consistent color for each list based on its title
    color_map = {
        'Inbox': 'blue',
        'Work': 'cyan',
        'Personal': 'green',
        'Shopping': 'yellow',
        'Projects': 'magenta'
    }
    
    # Try to find a matching color based on list title
    for keyword, color in color_map.items():
        if keyword.lower() in list_title.lower():
            return color
    
    # Default color for other lists
    return 'white'

def _get_priority_icon(priority) -> str:
    """Get appropriate icon for priority level"""
    if isinstance(priority, str):
        priority_value = priority.lower()
    else:
        priority_value = priority.value.lower() if hasattr(priority, 'value') else str(priority).lower()
    
    priority_indicators = {
        'low': '🔽',
        'medium': '🔸', 
        'high': '🔺',
        'critical': '💥'
    }
    
    return priority_indicators.get(priority_value, '🔸')

def _format_due_date(due) -> str:
    """Format due date for display with proper timezone handling"""
    if not due:
        return ""
    
    try:
        # Convert to datetime if we have a string
        if isinstance(due, str):
            due = datetime.fromisoformat(due)
        
        # Normalize datetime to timezone-naive for comparison
        due = _normalize_datetime(due)
        
        # Convert to date if we have a datetime
        if hasattr(due, 'date'):
            due_date = due.date()
        else:
            due_date = due
            
        # Get current date using the same timezone-naive approach
        current_date = _normalize_datetime(datetime.now()).date()
        
        days_diff = (due_date - current_date).days
        
        if days_diff == 0:
            return " (Today)"
        elif days_diff == 1:
            return " (Tomorrow)"
        elif days_diff < 0:
            return f" ({abs(days_diff)} days overdue)"
        else:
            return f" (in {days_diff} days)"
    except Exception as e:
        return ""

def _get_status_color(status) -> str:
    """Get color for task status"""
    if isinstance(status, str):
        status_value = status.lower()
    else:
        status_value = status.value.lower() if hasattr(status, 'value') else str(status).lower()
    
    color_map = {
        'pending': 'white',
        'in_progress': 'cyan',
        'completed': 'green',
        'waiting': 'yellow',
        'deleted': 'red'
    }
    
    return color_map.get(status_value, 'white')


def _filter_tasks_by_time(tasks: List[Task], filter_type: str) -> List[Task]:
    """Filter tasks by time period"""
    # Use timezone-naive datetimes for comparison to avoid timezone issues
    now = datetime.now().replace(tzinfo=None)
    
    def _task_in_time_period(task: Task, start_time, end_time) -> bool:
        """Check if a task falls within the specified time period based on due, created, or modified dates"""
        # Check due date first
        if task.due and start_time <= _normalize_datetime(task.due) < end_time:
            return True
        
        # Check created date
        if task.created_at and start_time <= _normalize_datetime(task.created_at) < end_time:
            return True
            
        # Check modified date
        if task.modified_at and start_time <= _normalize_datetime(task.modified_at) < end_time:
            return True
            
        return False
    
    if filter_type == 'today':
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        return [t for t in tasks if _task_in_time_period(t, start_of_day, end_of_day)]
    
    elif filter_type == 'this_week':
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(weeks=1)
        return [t for t in tasks if _task_in_time_period(t, start_of_week, end_of_week)]
    
    elif filter_type == 'this_month':
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            end_of_month = now.replace(month=now.month + 1, day=1)
        return [t for t in tasks if _task_in_time_period(t, start_of_month, end_of_month)]
    
    elif filter_type == 'last_month':
        if now.month == 1:
            start_of_month = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_month = now.replace(year=now.year, month=1, day=1)
        else:
            start_of_month = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_month = now.replace(day=1)
        return [t for t in tasks if _task_in_time_period(t, start_of_month, end_of_month)]
    
    elif filter_type == 'last_3m':
        start_date = now - timedelta(days=90)
        return [t for t in tasks if _task_in_time_period(t, start_date, now)]
    
    elif filter_type == 'last_6m':
        start_date = now - timedelta(days=180)
        return [t for t in tasks if _task_in_time_period(t, start_date, now)]
    
    elif filter_type == 'last_year':
        start_date = now - timedelta(days=365)
        return [t for t in tasks if _task_in_time_period(t, start_date, now)]
    
    return tasks

#!/usr/bin/env python3
"""
List command for the Google Tasks CLI application.
"""

import click
from datetime import datetime, timedelta
from typing import List
from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.utils.display import display_tasks_grouped_by_list

logger = setup_logger(__name__)

# State for interactive mode
class TaskState:
    """Hold state for interactive mode"""
    def __init__(self):
        self.tasks = []
        self.task_number_to_id = {}
        self.task_id_to_number = {}
    
    def set_tasks(self, tasks: List[Task]):
        """Set tasks and create mappings"""
        self.tasks = tasks
        self.task_number_to_id = {}
        self.task_id_to_number = {}
        
        for i, task in enumerate(tasks, 1):
            self.task_number_to_id[i] = task.id
            self.task_id_to_number[task.id] = i
    
    def get_task_by_number(self, number: int) -> Task:
        """Get task by its display number"""
        if number in self.task_number_to_id:
            task_id = self.task_number_to_id[number]
            for task in self.tasks:
                if task.id == task_id:
                    return task
        return None
    
    def get_number_by_task_id(self, task_id: str) -> int:
        """Get display number by task ID"""
        return self.task_id_to_number.get(task_id)

# Global state for interactive mode
task_state = TaskState()


@click.command()
@click.argument('list_filter', required=False)
@click.option('--status', '-s', type=click.Choice(['pending', 'in_progress', 'completed', 'waiting', 'deleted']), 
              help='Filter tasks by status')
@click.option('--priority', '-p', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              help='Filter tasks by priority')
@click.option('--project', '-P', help='Filter tasks by project')
@click.option('--recurring', '-r', is_flag=True, help='Show only recurring tasks')
@click.option('--filter', '-f', 'time_filter', 
              type=click.Choice(['today', 'this_week', 'this_month', 'last_month', 'last_3m', 'last_6m', 'last_year']),
              help='Filter tasks by time period')
@click.option('--search', '-S', help='Search tasks by title, description, or notes')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def list(ctx, list_filter, status, priority, project, recurring, time_filter, search, account):
    """List tasks with optional filtering.
    
    LIST_FILTER: Filter tasks by list name (partial match, case insensitive)
    """
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'json')
    
    # Determine the account to use
    if account:
        # Explicitly specified account
        account_name = account
    else:
        # Check context object for account
        account_name = ctx.obj.get('account_name')
    
    logger.info(f"Listing tasks {'(Google Tasks)' if use_google_tasks else '(Local)'} for account: {account_name or 'default'}")
    
    # Create task manager with account support
    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend,
        account_name=account_name
    )
    
    # Convert string parameters to enums
    status_enum = None
    if status:
        status_enum = TaskStatus[status.upper()]
    
    priority_enum = None
    if priority:
        priority_enum = Priority[priority.upper()]
    
    # Get tasks with all filters
    try:
        tasks = task_manager.list_tasks(
            list_filter=list_filter,
            status=status_enum,
            priority=priority_enum,
            project=project,
            recurring=recurring if recurring else None,
            search=search
        )
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        click.echo(f"❌ Error retrieving tasks: {e}")
        return
    
    # Apply time filter
    if time_filter:
        tasks = _filter_tasks_by_time(tasks, time_filter)
    
    # For Google Tasks, we need to filter for incomplete tasks by default
    if use_google_tasks:
        tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
    
    # Display tasks grouped by list names with color coding
    display_tasks_grouped_by_list(tasks)
    
    # Store current tasks in task_state for interactive mode
    task_state.set_tasks(tasks)

