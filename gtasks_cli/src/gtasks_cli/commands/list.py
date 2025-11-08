#!/usr/bin/env python3
"""
List command for Google Tasks CLI
"""

import click
from datetime import datetime, timedelta
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Priority

class TaskStateManager:
    """Manage task state for interactive mode"""
    def __init__(self):
        self.numbered_tasks = []
    
    def set_tasks(self, tasks):
        """Set the current list of tasks"""
        self.numbered_tasks[:] = tasks
    
    def get_tasks(self):
        """Get the current list of tasks"""
        return self.numbered_tasks[:]
    
    def get_task_by_index(self, index):
        """Get a task by its 1-based index"""
        if 1 <= index <= len(self.numbered_tasks):
            return self.numbered_tasks[index - 1]
        return None

# Set up logger
logger = setup_logger(__name__)

# Global task state manager
task_state = TaskStateManager()


@click.command()
@click.argument('list_filter', required=False, type=str)
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'waiting', 'deleted']), 
              help='Filter by status')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              help='Filter by priority')
@click.option('--project', help='Filter by project')
@click.option('--recurring', '-r', is_flag=True, help='Show only recurring tasks')
@click.option('--filter', 'time_filter', type=click.Choice([
    'today', 'this_week', 'this_month', 'last_month', 'last_3m', 'last_6m', 'last_year'
]), help='Filter by time period')
@click.option('--search', help='Search in task title and description')
@click.pass_context
def list(ctx, list_filter, status, priority, project, recurring, time_filter, search):
    """List all tasks, optionally filtered by task list name
    
    \b
    Examples:
      # List all tasks
      gtasks list
      
      # List tasks from lists containing "My" in the name
      gtasks list "My"
      
      # List only pending tasks
      gtasks list --status pending
      
      # List high priority tasks from lists containing "Work"
      gtasks list "Work" --priority high
      
      # List tasks for a specific project
      gtasks list --project "Project X"
      
      # List only recurring tasks
      gtasks list --recurring
      
      # List tasks from the last 3 months with "meeting" in title or description
      gtasks list --filter last_3m --search "meeting"
      
      # List pending tasks from lists with "Work" in name, from this month
      gtasks list "Work" --status pending --filter this_month
      
      # List using Google Tasks directly
      gtasks list -g
    """
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Listing tasks {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    from gtasks_cli.models.task import TaskStatus
    
    # Create task manager
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    # Convert string parameters to enums where needed
    status_enum = TaskStatus(status) if status else None
    priority_enum = Priority(priority) if priority else None
    
    if use_google_tasks:
        # For Google Tasks, we can filter by list name
        from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
        client = GoogleTasksClient()
        tasklists = client.list_tasklists()
        
        # Filter tasklists by name if filter provided
        if list_filter:
            tasklists = [tl for tl in tasklists if list_filter.lower() in tl.get('title', '').lower()]
        
        if not tasklists:
            click.echo("No matching task lists found.")
            return
        
        total_tasks = 0
        all_tasks = []
        for tasklist in tasklists:
            tasklist_id = tasklist['id']
            tasklist_title = tasklist.get('title', 'Untitled List')
            
            tasks = task_manager.list_tasks_by_list(
                tasklist_id=tasklist_id,
                status=status_enum,
                priority=priority_enum,
                project=project
            )
            
            # Apply additional filters
            tasks = _apply_additional_filters(tasks, time_filter, search, recurring)
            
            if tasks:
                click.echo(f"\n{tasklist_title}")
                _display_tasks(tasks, start_number=total_tasks + 1)
                all_tasks.extend(tasks)
                total_tasks += len(tasks)
            else:
                click.echo(f"\n{tasklist_title}")
                click.echo("  (No tasks)")
        
        # Store tasks for interactive mode
        task_state.set_tasks(all_tasks)
        
        # Summary
        click.echo(f"\nSummary: {len(tasklists)} list(s) with {total_tasks} total task(s)")
    else:
        # For local tasks, list_filter is not applicable
        tasks = task_manager.list_tasks(
            status=status_enum,
            priority=priority_enum,
            project=project
        )
        
        # Apply additional filters
        tasks = _apply_additional_filters(tasks, time_filter, search, recurring)
        
        if not tasks:
            click.echo("No tasks found.")
            return
        
        click.echo("Tasks")
        _display_tasks(tasks)
        
        # Store tasks for interactive mode
        task_state.set_tasks(tasks)


def _apply_additional_filters(tasks, time_filter, search, recurring):
    """Apply additional filters to tasks"""
    # Filter for recurring tasks if requested
    if recurring:
        tasks = [task for task in tasks if task.is_recurring]
    
    # Apply time filter
    if time_filter:
        tasks = _filter_by_time(tasks, time_filter)
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        tasks = [task for task in tasks 
                if search_lower in (task.title or '').lower() 
                or search_lower in (task.description or '').lower()
                or search_lower in (task.notes or '').lower()]
    
    return tasks


def _filter_by_time(tasks, time_filter):
    """Filter tasks by time period"""
    # Use timezone-naive datetimes for comparison to avoid timezone issues
    now = datetime.now().replace(tzinfo=None)
    
    if time_filter == 'today':
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        tasks = [t for t in tasks if t.due and start_of_day <= _normalize_datetime(t.due) < end_of_day]
    
    elif time_filter == 'this_week':
        # Start of week (Monday)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=7)
        tasks = [t for t in tasks if t.due and start_of_week <= _normalize_datetime(t.due) < end_of_week]
    
    elif time_filter == 'this_month':
        # Start of month
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # End of month
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            end_of_month = now.replace(month=now.month + 1, day=1)
        tasks = [t for t in tasks if t.due and start_of_month <= _normalize_datetime(t.due) < end_of_month]
    
    elif time_filter == 'last_month':
        # Start of last month
        if now.month == 1:
            start_of_month = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_of_month = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # End of last month
        end_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        tasks = [t for t in tasks if t.due and start_of_month <= _normalize_datetime(t.due) < end_of_month]
    
    elif time_filter == 'last_3m':
        # Start of 3 months ago
        months_ago = now.month - 3
        years_ago = now.year
        while months_ago <= 0:
            months_ago += 12
            years_ago -= 1
        start_of_period = now.replace(year=years_ago, month=months_ago, day=1, hour=0, minute=0, second=0, microsecond=0)
        # End is today
        end_of_period = now
        tasks = [t for t in tasks if t.due and start_of_period <= _normalize_datetime(t.due) <= end_of_period]
    
    elif time_filter == 'last_6m':
        # Start of 6 months ago
        months_ago = now.month - 6
        years_ago = now.year
        while months_ago <= 0:
            months_ago += 12
            years_ago -= 1
        start_of_period = now.replace(year=years_ago, month=months_ago, day=1, hour=0, minute=0, second=0, microsecond=0)
        # End is today
        end_of_period = now
        tasks = [t for t in tasks if t.due and start_of_period <= _normalize_datetime(t.due) <= end_of_period]
    
    elif time_filter == 'last_year':
        # Start of last year
        start_of_year = now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        # End of last year
        end_of_year = now.replace(year=now.year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        tasks = [t for t in tasks if t.due and start_of_year <= _normalize_datetime(t.due) < end_of_year]
    
    return tasks


def _normalize_datetime(dt):
    """Normalize datetime to timezone-naive for comparison"""
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        # Convert to naive datetime by removing timezone info
        return dt.replace(tzinfo=None)
    return dt


def _display_tasks(tasks, start_number=1):
    """Helper function to display tasks with consistent formatting"""
    for i, task in enumerate(tasks, start_number):
        # For enum values, we need to check if they are already strings or enum instances
        status_value = task.status if isinstance(task.status, str) else task.status.value
        priority_value = task.priority if isinstance(task.priority, str) else task.priority.value
        
        status_icon = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'waiting': '⏸️',
            'deleted': '🗑️'
        }.get(status_value, '❓')
        
        priority_icon = {
            'low': '🔽',
            'medium': '🔸',
            'high': '🔺',
            'critical': '💥'
        }.get(priority_value, '🔹')
        
        # Format due date if present
        due_info = ""
        if task.due:
            due_info = f" 📅 {task.due.strftime('%Y-%m-%d')}"
        
        # Format project if present
        project_info = ""
        if task.project:
            project_info = f" 📁 {task.project}"
        
        # Format tags if present
        tags_info = ""
        if task.tags:
            tags_info = f" 🏷️  {', '.join(task.tags)}"
        
        # Format recurring info
        recurring_info = ""
        if task.is_recurring:
            recurring_info = " 🔁"
        
        # Display task with number and ID for reference
        click.echo(f"  {i:2d}. {task.id[:8]}: {status_icon} {priority_icon} {task.title}{due_info}{project_info}{tags_info}{recurring_info}")
        
        # Show description if present
        if task.description:
            # Wrap description to fit nicely
            desc_lines = []
            words = task.description.split()
            line = ""
            for word in words:
                if len(line + word) <= 60:
                    line += word + " "
                else:
                    desc_lines.append(line.strip())
                    line = word + " "
            if line:
                desc_lines.append(line.strip())
            
            for j, line in enumerate(desc_lines):
                prefix = "  │    " if j == 0 else "  │      "
                click.echo(f"{prefix}{line}")
        
        # Show notes if present and different from description
        if task.notes and task.notes != task.description:
            notes_lines = []
            words = task.notes.split()
            line = ""
            for word in words:
                if len(line + word) <= 60:
                    line += word + " "
                else:
                    notes_lines.append(line.strip())
                    line = word + " "
            if line:
                notes_lines.append(line.strip())
            
            for j, line in enumerate(notes_lines):
                prefix = "  │    📝 " if j == 0 else "  │       "
                click.echo(f"{prefix}{line}")