#!/usr/bin/env python3
"""
Interactive mode for Google Tasks CLI
"""

import click
import shlex
from typing import List
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task, TaskStatus, Priority

logger = setup_logger(__name__)

# Try to import prompt_toolkit for better command line experience
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False


@click.command()
@click.pass_context
def interactive(ctx):
    """Start interactive mode for task management.
    
    In interactive mode, tasks are numbered sequentially and you can perform
    operations on them using these numbers.
    
    \b
    Commands in interactive mode:
      view <number>     - View task details
      done <number>     - Mark task as completed
      delete <number>   - Delete a task
      update <number>   - Update a task
      add               - Add a new task
      list              - List all tasks
      list [filter]     - List tasks with filters (same as gtasks list command)
      search <query>    - Search tasks
      help              - Show this help
      quit/exit         - Exit interactive mode
    """
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Starting interactive mode {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    from gtasks_cli.commands.list import task_state
    
    # Create task manager
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    # Get all tasks
    tasks = task_manager.list_tasks()
    
    if not tasks:
        click.echo("No tasks found.")
        return
    
    # Display tasks with numbers
    _display_numbered_tasks(tasks)
    
    # Store current tasks in task_state
    task_state.set_tasks(tasks)
    
    # Command history for prompt_toolkit
    if HAS_PROMPT_TOOLKIT:
        history = InMemoryHistory()
    
    # Enter interactive loop
    while True:
        try:
            # Use prompt_toolkit for better command line experience if available
            if HAS_PROMPT_TOOLKIT:
                command_input = prompt(
                    "\nEnter command: ",
                    history=history if HAS_PROMPT_TOOLKIT else None,
                    auto_suggest=AutoSuggestFromHistory() if HAS_PROMPT_TOOLKIT else None
                ).strip()
            else:
                command_input = click.prompt("\nEnter command", type=str).strip()
                
            if not command_input:
                continue
                
            # Parse command with shlex to handle quotes properly
            try:
                command_parts = shlex.split(command_input)
            except ValueError as e:
                click.echo(f"Error parsing command: {e}")
                continue
                
            if not command_parts:
                continue
                
            cmd = command_parts[0].lower()
            
            if cmd in ['quit', 'exit']:
                click.echo("Exiting interactive mode.")
                break
            elif cmd == 'list':
                # Handle list command with all its options
                if len(command_parts) > 1:
                    # Parse list command arguments manually
                    list_filter = None
                    status = None
                    priority = None
                    project = None
                    recurring = False
                    time_filter = None
                    search_query = None
                    
                    # Parse arguments
                    i = 1
                    while i < len(command_parts):
                        arg = command_parts[i]
                        if arg.startswith('--'):
                            option = arg[2:]  # Remove --
                            if option == 'status' and i + 1 < len(command_parts):
                                status = command_parts[i + 1]
                                i += 2
                            elif option == 'priority' and i + 1 < len(command_parts):
                                priority = command_parts[i + 1]
                                i += 2
                            elif option == 'project' and i + 1 < len(command_parts):
                                project = command_parts[i + 1]
                                i += 2
                            elif option == 'recurring':
                                recurring = True
                                i += 1
                            elif option == 'filter' and i + 1 < len(command_parts):
                                time_filter = command_parts[i + 1]
                                i += 2
                            elif option == 'search' and i + 1 < len(command_parts):
                                search_query = command_parts[i + 1]
                                i += 2
                            else:
                                # Unknown option, skip
                                i += 1
                        else:
                            # Positional argument (list filter)
                            if list_filter is None:
                                list_filter = arg
                            i += 1
                    
                    # Apply filters using task manager
                    try:
                        # Convert string parameters to enums where needed
                        status_enum = TaskStatus(status) if status else None
                        priority_enum = Priority(priority) if priority else None
                        
                        # Get filtered tasks
                        filtered_tasks = task_manager.list_tasks(
                            status=status_enum,
                            priority=priority_enum,
                            project=project
                        )
                        
                        # Apply additional filters manually
                        if recurring:
                            filtered_tasks = [task for task in filtered_tasks if task.is_recurring]
                            
                        # Apply time filter
                        if time_filter:
                            filtered_tasks = _filter_by_time(filtered_tasks, time_filter)
                            
                        # Apply search filter
                        if search_query:
                            search_lower = search_query.lower()
                            filtered_tasks = [
                                task for task in filtered_tasks 
                                if search_lower in (task.title or '').lower() 
                                or search_lower in (task.description or '').lower()
                                or search_lower in (task.notes or '').lower()
                            ]
                        
                        # Display filtered tasks
                        _display_numbered_tasks(filtered_tasks)
                        task_state.set_tasks(filtered_tasks)
                    except Exception as e:
                        click.echo(f"Error applying filters: {e}")
                else:
                    # Simple list all
                    tasks = task_manager.list_tasks()
                    _display_numbered_tasks(tasks)
                    task_state.set_tasks(tasks)
            elif cmd == 'view':
                if len(command_parts) < 2:
                    click.echo("Usage: view <number>")
                    continue
                    
                try:
                    task_num = int(command_parts[1])
                    task = task_state.get_task_by_index(task_num)
                    if task:
                        _view_task_details(task)
                    else:
                        click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.get_tasks())}.")
                except ValueError:
                    click.echo("Invalid task number. Please enter a valid integer.")
            elif cmd == 'done':
                if len(command_parts) < 2:
                    click.echo("Usage: done <number>")
                    continue
                    
                try:
                    task_num = int(command_parts[1])
                    task = task_state.get_task_by_index(task_num)
                    if task:
                        if task_manager.complete_task(task.id):
                            click.echo(f"Task '{task.title}' marked as completed.")
                            # Refresh task list
                            tasks = task_manager.list_tasks()
                            _display_numbered_tasks(tasks)
                            task_state.set_tasks(tasks)
                        else:
                            click.echo("Failed to mark task as completed.")
                    else:
                        click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.get_tasks())}.")
                except ValueError:
                    click.echo("Invalid task number. Please enter a valid integer.")
            elif cmd == 'delete':
                if len(command_parts) < 2:
                    click.echo("Usage: delete <number>")
                    continue
                    
                try:
                    task_num = int(command_parts[1])
                    task = task_state.get_task_by_index(task_num)
                    if task:
                        confirm = click.confirm(f"Are you sure you want to delete '{task.title}'?")
                        if confirm:
                            if task_manager.delete_task(task.id):
                                click.echo(f"Task '{task.title}' deleted.")
                                # Refresh task list
                                tasks = task_manager.list_tasks()
                                _display_numbered_tasks(tasks)
                                task_state.set_tasks(tasks)
                            else:
                                click.echo("Failed to delete task.")
                    else:
                        click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.get_tasks())}.")
                except ValueError:
                    click.echo("Invalid task number. Please enter a valid integer.")
            elif cmd == 'add':
                title = click.prompt("Task title")
                description = click.prompt("Task description (optional)", default="", show_default=False)
                if not description:
                    description = None
                    
                if task_manager.create_task(title=title, description=description):
                    click.echo("Task created successfully.")
                    # Refresh task list
                    tasks = task_manager.list_tasks()
                    _display_numbered_tasks(tasks)
                    task_state.set_tasks(tasks)
                else:
                    click.echo("Failed to create task.")
            elif cmd == 'search':
                if len(command_parts) < 2:
                    click.echo("Usage: search <query>")
                    continue
                    
                query = " ".join(command_parts[1:])
                search_results = task_manager.search_tasks(query)
                if search_results:
                    click.echo(f"\nSearch results for '{query}':")
                    _display_numbered_tasks(search_results)
                    task_state.set_tasks(search_results)
                else:
                    click.echo(f"No tasks found matching '{query}'.")
                    # Keep current tasks unchanged
            elif cmd == 'help':
                click.echo("""
Interactive Mode Commands:
  view <number>     - View task details
  done <number>     - Mark task as completed
  delete <number>   - Delete a task
  update <number>   - Update a task (not yet implemented)
  add               - Add a new task
  list              - List all tasks
  list [filters]    - List tasks with filters (same as gtasks list command)
  search <query>    - Search tasks
  help              - Show this help
  quit/exit         - Exit interactive mode
  
List Filter Options (same as gtasks list):
  LIST_FILTER       - Filter task lists by name (e.g., "My")
  --status STATUS   - Filter by status (pending, completed, etc.)
  --priority LEVEL  - Filter by priority (low, medium, high, critical)
  --project NAME    - Filter by project
  --recurring       - Show only recurring tasks
  --filter PERIOD   - Filter by time (today, this_week, this_month, last_3m, etc.)
  --search QUERY    - Search in title, description, notes
                """)
            else:
                click.echo(f"Unknown command: {cmd}. Type 'help' for available commands.")
                
        except (KeyboardInterrupt, EOFError):
            click.echo("\nExiting interactive mode.")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            click.echo(f"An error occurred: {e}")


def _filter_by_time(tasks, time_filter):
    """Filter tasks by time period"""
    from datetime import datetime, timedelta
    
    # Use timezone-naive datetimes for comparison to avoid timezone issues
    now = datetime.now().replace(tzinfo=None)
    
    if time_filter == 'today':
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        tasks = [t for t in tasks if t.due and _normalize_datetime(t.due) >= start_of_day and _normalize_datetime(t.due) < end_of_day]
    
    elif time_filter == 'this_week':
        # Start of week (Monday)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=7)
        tasks = [t for t in tasks if t.due and _normalize_datetime(t.due) >= start_of_week and _normalize_datetime(t.due) < end_of_week]
    
    elif time_filter == 'this_month':
        # Start of month
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # End of month
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            end_of_month = now.replace(month=now.month + 1, day=1)
        tasks = [t for t in tasks if t.due and _normalize_datetime(t.due) >= start_of_month and _normalize_datetime(t.due) < end_of_month]
    
    elif time_filter == 'last_month':
        # Start of last month
        if now.month == 1:
            start_of_month = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_of_month = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # End of last month
        end_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        tasks = [t for t in tasks if t.due and _normalize_datetime(t.due) >= start_of_month and _normalize_datetime(t.due) < end_of_month]
    
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
        tasks = [t for t in tasks if t.due and _normalize_datetime(t.due) >= start_of_period and _normalize_datetime(t.due) <= end_of_period]
    
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
        tasks = [t for t in tasks if t.due and _normalize_datetime(t.due) >= start_of_period and _normalize_datetime(t.due) <= end_of_period]
    
    elif time_filter == 'last_year':
        # Start of last year
        start_of_year = now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        # End of last year
        end_of_year = now.replace(year=now.year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        tasks = [t for t in tasks if t.due and _normalize_datetime(t.due) >= start_of_year and _normalize_datetime(t.due) < end_of_year]
    
    return tasks


def _normalize_datetime(dt):
    """Normalize datetime to timezone-naive for comparison"""
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        # Convert to naive datetime by removing timezone info
        return dt.replace(tzinfo=None)
    return dt


def _display_numbered_tasks(tasks: List[Task]):
    """Display tasks with sequential numbers"""
    click.echo("\nTasks:")
    for i, task in enumerate(tasks, 1):
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
        
        # Display task with number
        click.echo(f"  {i:2d}. {task.id[:8]}: {status_icon} {priority_icon} {task.title}{due_info}{project_info}{tags_info}{recurring_info}")


def _view_task_details(task: Task):
    """Display detailed information about a task"""
    click.echo(f"\nTask Details:")
    click.echo(f"  ID: {task.id}")
    click.echo(f"  Title: {task.title}")
    
    if task.description:
        click.echo(f"  Description: {task.description}")
        
    if task.notes:
        click.echo(f"  Notes: {task.notes}")
        
    if task.due:
        click.echo(f"  Due Date: {task.due}")
        
    # Display status
    status_value = task.status if isinstance(task.status, str) else task.status.value
    click.echo(f"  Status: {status_value}")
    
    # Display priority
    priority_value = task.priority if isinstance(task.priority, str) else task.priority.value
    click.echo(f"  Priority: {priority_value}")
    
    if task.project:
        click.echo(f"  Project: {task.project}")
        
    if task.tags:
        click.echo(f"  Tags: {', '.join(task.tags)}")
        
    if task.dependencies:
        click.echo(f"  Dependencies: {', '.join(task.dependencies)}")
        
    if task.is_recurring:
        click.echo(f"  Recurrence Rule: {task.recurrence_rule}")
        
    click.echo(f"  Created: {task.created_at}")
    if task.modified_at:
        click.echo(f"  Modified: {task.modified_at}")
    if hasattr(task, 'completed_at') and task.completed_at:
        click.echo(f"  Completed: {task.completed_at}")