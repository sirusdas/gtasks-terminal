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
            
            # Format created, modified, and due dates
            dates_str = ""
            if task.due:
                due_date_str = task.due.strftime('%Y-%m-%d') if hasattr(task.due, 'strftime') else str(task.due)[:10]
                dates_str += f" [D:{due_date_str}]"
            
            if task.created_at:
                dates_str += f" [C:{task.created_at.strftime('%Y-%m-%d')}]"
            if task.modified_at:
                dates_str += f" [M:{task.modified_at.strftime('%Y-%m-%d')}]"
            
            # Build the task line
            task_line = f"{i:2d}. {priority_icon} {task.title}{due_str}{dates_str}"
            
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
    
    # Parse filter type to check if it specifies a date field
    # Format: "this_month:due_date" or "this_week:created_at"
    if ':' in filter_type:
        period, date_field = filter_type.split(':', 1)
        date_field = date_field.lower()
    else:
        period = filter_type
        date_field = None  # Will use all date fields
    
    # Check if period is a custom date or date range in DDMMYYYY format
    if _is_custom_date_format(period):
        return _filter_tasks_by_custom_date(tasks, period, date_field)
    
    def _task_in_time_period(task: Task, start_time, end_time, specific_field=None) -> bool:
        """Check if a task falls within the specified time period based on specified or all date fields"""
        # If a specific field is requested, only check that field
        if specific_field:
            if specific_field == 'due_date' and task.due:
                return start_time <= _normalize_datetime(task.due) < end_time
            elif specific_field == 'created_at' and task.created_at:
                return start_time <= _normalize_datetime(task.created_at) < end_time
            elif specific_field == 'modified_at' and task.modified_at:
                return start_time <= _normalize_datetime(task.modified_at) < end_time
            return False
            
        # Otherwise check all date fields
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
    
    if period == 'today':
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        return [t for t in tasks if _task_in_time_period(t, start_of_day, end_of_day, date_field)]
    
    elif period == 'this_week':
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(weeks=1)
        return [t for t in tasks if _task_in_time_period(t, start_of_week, end_of_week, date_field)]
    
    elif period == 'this_month':
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            end_of_month = now.replace(month=now.month + 1, day=1)
        return [t for t in tasks if _task_in_time_period(t, start_of_month, end_of_month, date_field)]
    
    elif period == 'last_month':
        if now.month == 1:
            start_of_month = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_month = now.replace(year=now.year, month=1, day=1)
        else:
            start_of_month = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_month = now.replace(day=1)
        return [t for t in tasks if _task_in_time_period(t, start_of_month, end_of_month, date_field)]
    
    elif period == 'last_3m':
        start_date = now - timedelta(days=90)
        return [t for t in tasks if _task_in_time_period(t, start_date, now, date_field)]
    
    elif period == 'last_6m':
        start_date = now - timedelta(days=180)
        return [t for t in tasks if _task_in_time_period(t, start_date, now, date_field)]
    
    elif period == 'last_year':
        start_date = now - timedelta(days=365)
        return [t for t in tasks if _task_in_time_period(t, start_date, now, date_field)]
    
    return tasks


def _is_custom_date_format(period: str) -> bool:
    """Check if the period string represents a custom date or date range in DDMMYYYY format"""
    # Check for single date format: DDMMYYYY
    if len(period) == 8 and period.isdigit():
        return True
    
    # Check for date range format: DDMMYYYY-DDMMYYYY
    if '-' in period and len(period.split('-')) == 2:
        start_date, end_date = period.split('-')
        if len(start_date) == 8 and len(end_date) == 8 and start_date.isdigit() and end_date.isdigit():
            return True
    
    return False


def _parse_date_string(date_str: str) -> datetime:
    """Parse DDMMYYYY format date string into datetime object"""
    if len(date_str) != 8 or not date_str.isdigit():
        raise ValueError("Date must be in DDMMYYYY format")
    
    day = int(date_str[0:2])
    month = int(date_str[2:4])
    year = int(date_str[4:8])
    
    return datetime(year, month, day)


def _filter_tasks_by_custom_date(tasks: List[Task], period: str, date_field: str = None) -> List[Task]:
    """Filter tasks by custom date or date range in DDMMYYYY format"""
    def _task_matches_date(task: Task, start_date: datetime, end_date: datetime, specific_field: str = None) -> bool:
        """Check if a task falls within the specified date range based on specified or all date fields"""
        # If a specific field is requested, only check that field
        if specific_field:
            if specific_field == 'due_date' and task.due:
                task_date = _normalize_datetime(task.due).date()
                return start_date.date() <= task_date <= end_date.date()
            elif specific_field == 'created_at' and task.created_at:
                task_date = _normalize_datetime(task.created_at).date()
                return start_date.date() <= task_date <= end_date.date()
            elif specific_field == 'modified_at' and task.modified_at:
                task_date = _normalize_datetime(task.modified_at).date()
                return start_date.date() <= task_date <= end_date.date()
            return False
            
        # Otherwise check all date fields
        # Check due date
        if task.due:
            task_date = _normalize_datetime(task.due).date()
            if start_date.date() <= task_date <= end_date.date():
                return True
        
        # Check created date
        if task.created_at:
            task_date = _normalize_datetime(task.created_at).date()
            if start_date.date() <= task_date <= end_date.date():
                return True
            
        # Check modified date
        if task.modified_at:
            task_date = _normalize_datetime(task.modified_at).date()
            if start_date.date() <= task_date <= end_date.date():
                return True
            
        return False
    
    # Handle date range format: DDMMYYYY-DDMMYYYY
    if '-' in period:
        start_date_str, end_date_str = period.split('-')
        start_date = _parse_date_string(start_date_str)
        end_date = _parse_date_string(end_date_str)
        # Set time to start of start day and end of end day
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # Handle single date format: DDMMYYYY
        target_date = _parse_date_string(period)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return [t for t in tasks if _task_matches_date(t, start_date, end_date, date_field)]


def _sort_tasks(tasks: List[Task], sort_field: str) -> List[Task]:
    """Sort tasks by the specified field.
    
    Supports:
    - 'field' (ascending)
    - 'field:asc' (ascending)
    - 'field:desc' (descending)
    - '-field' (descending)
    
    Aliases:
    - 'due_date' -> 'due'
    - 'created_at' -> 'created'
    - 'modified_at' -> 'modified'
    """
    sorted_tasks = tasks.copy()
    
    # Parse sort field and direction
    reverse = False
    
    # Check for :desc or :asc suffix
    if ':' in sort_field:
        field, direction = sort_field.rsplit(':', 1)
        direction = direction.lower().strip()
        if direction == 'desc':
            reverse = True
        elif direction == 'asc':
            reverse = False
        sort_field = field.strip()
    # Check for - prefix
    elif sort_field.startswith('-'):
        reverse = True
        sort_field = sort_field[1:]
        
    # Normalize field names
    sort_field = sort_field.lower()
    field_map = {
        'due_date': 'due',
        'created_at': 'created',
        'modified_at': 'modified'
    }
    sort_field = field_map.get(sort_field, sort_field)
    
    if sort_field == 'due':
        # Sort by due date, with tasks without due dates at the end (or beginning if reversed? usually end is better for "no due date")
        # For consistent sorting:
        # Ascending: Earliest due date first. No due date last.
        # Descending: Latest due date first. No due date last.
        # To handle None values correctly in Python 3, we need a custom key
        if reverse:
            # For descending, we want latest dates first. None values can go last.
            sorted_tasks.sort(key=lambda t: (t.due is None, t.due), reverse=True)
        else:
            # For ascending, we want earliest dates first. None values last.
            sorted_tasks.sort(key=lambda t: (t.due is None, t.due))
            
    elif sort_field == 'created':
        # Sort by creation date
        sorted_tasks.sort(key=lambda t: t.created_at, reverse=reverse)
    elif sort_field == 'modified':
        # Sort by modification date
        sorted_tasks.sort(key=lambda t: t.modified_at, reverse=reverse)
    elif sort_field == 'priority':
        # Sort by priority (critical, high, medium, low)
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        # If reverse is True (descending), we might want Low to Critical? 
        # Standard "descending priority" usually means Highest first (Critical -> Low).
        # But our default sort (ascending index) does Critical(0) -> Low(3).
        # So "priority:desc" should probably reverse that to Low -> Critical.
        # Let's stick to Python's sort reverse.
        sorted_tasks.sort(key=lambda t: priority_order.get(t.priority.value if hasattr(t.priority, 'value') else t.priority, 4), reverse=reverse)
    elif sort_field == 'title':
        # Sort by title alphabetically
        sorted_tasks.sort(key=lambda t: t.title.lower(), reverse=reverse)
        
    return sorted_tasks


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
              help='Filter tasks by time period. '
                   'Use format like "this_month", "this_week", etc. '
                   'To filter by a specific date field, use "this_month:due_date", '
                   '"this_week:created_at", or "this_month:modified_at". '
                   'Supported periods: today, this_week, this_month, last_month, '
                   'last_3m, last_6m, last_year. '
                   'Custom date formats: DDMMYYYY for a specific date or '
                   'DDMMYYYY-DDMMYYYY for a date range.')
@click.option('--order-by', '-o', 'order_by',
              help='Order tasks by field (due, created, modified, priority, title). Supports :asc/:desc suffix (e.g. due_date:desc).')
@click.option('--search', '-S', help='Search tasks by title, description, or notes')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def list(ctx, list_filter, status, priority, project, recurring, time_filter, search, account, order_by):
    """List tasks with optional filtering.
    
    LIST_FILTER: Filter tasks by list name (partial match, case insensitive)
    """
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'json')
    
    # Determine the account to use
    account_name = account or ctx.obj.get('account')
    
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
    
    # Apply sorting if requested
    if order_by:
        tasks = _sort_tasks(tasks, order_by)
    
    # Display tasks grouped by list names with color coding
    display_tasks_grouped_by_list(tasks)
    
    # Store current tasks in task_state for interactive mode
    task_state.set_tasks(tasks)

