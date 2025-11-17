"""
Module for handling initial commands in interactive mode
"""

import shlex
import click
from gtasks_cli.models.task import TaskStatus


def handle_initial_list_command(task_manager, list_args, use_google_tasks):
    """Handle initial list command with arguments"""
    from gtasks_cli.commands.list import _filter_tasks_by_time
    
    # Parse the list arguments
    try:
        # Parse with shlex to properly handle quoted strings
        args = shlex.split(list_args) if list_args else []
    except ValueError as e:
        click.echo(f"Error parsing list arguments: {e}")
        return []
        
    
    # Process arguments similar to the list command
    list_filter = None
    status_filter = None
    time_filter = None
    search_term = None
    project_filter = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ['--status', '-s'] and i + 1 < len(args):
            status_filter = args[i + 1]
            i += 2
        elif arg in ['--filter', '-f']:
            if i + 1 < len(args):
                time_filter = args[i + 1]
                i += 2
            else:
                # Handle case where --filter is the last argument
                time_filter = None
                i += 1
        elif arg in ['--search', '--query'] and i + 1 < len(args):
            search_term = args[i + 1]
            i += 2
        elif arg in ['--project', '-p'] and i + 1 < len(args):
            project_filter = args[i + 1]
            i += 2
        elif arg.startswith('--status='):
            status_filter = arg.split('=', 1)[1]
            i += 1
        elif arg.startswith('--filter='):
            time_filter = arg.split('=', 1)[1]
            i += 1
        elif arg.startswith('--search=') or arg.startswith('--query='):
            search_term = arg.split('=', 1)[1]
            i += 1
        elif arg.startswith('--project='):
            project_filter = arg.split('=', 1)[1]
            i += 1
        else:
            # Treat as list filter if it's the first argument and not a flag
            if list_filter is None and not arg.startswith('-'):
                # Collect all consecutive non-flag arguments as the list filter
                list_parts = [arg]
                j = i + 1
                while j < len(args) and not args[j].startswith('-'):
                    list_parts.append(args[j])
                    j += 1
                list_filter = ' '.join(list_parts)
                i = j
            # Otherwise treat as a general search term
            elif search_term is None:
                search_term = arg
                i += 1
            else:
                i += 1
    
    # Get tasks based on filters
    if use_google_tasks:
        # For Google Tasks, get all tasks
        tasks = task_manager.list_tasks()
    else:
        # Convert string status to enum if provided
        status_enum = None
        if status_filter:
            # Handle 'incomplete' as a special case
            if status_filter.lower() == 'incomplete':
                # For incomplete, we'll filter afterwards as it's not a single status
                status_enum = None
            else:
                try:
                    status_enum = TaskStatus(status_filter.lower())
                except ValueError:
                    # If not a valid status, we'll filter afterwards
                    status_enum = None
        
        # For local mode, get tasks with list and status filters if provided
        tasks = task_manager.list_tasks(list_filter=list_filter, status=status_enum)
    
    # Apply additional filters for special cases
    if status_filter:
        # Handle 'incomplete' as a special case - it means not completed
        if status_filter.lower() == 'incomplete':
            # Filter for all non-completed tasks
            tasks = [t for t in tasks if t.status != TaskStatus.COMPLETED]
        elif status_enum is None:
            # If we couldn't convert to enum, filter by string match
            tasks = [t for t in tasks if status_filter.lower() in str(t.status).lower()]
    elif not status_filter:
        # By default, filter for incomplete tasks (same as regular interactive mode)
        # But only if we didn't already filter by status in the task manager
        tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
    
    if time_filter:
        tasks = _filter_tasks_by_time(tasks, time_filter)
    
    if search_term:
        tasks = [t for t in tasks if search_term.lower() in t.title.lower() or 
                 (t.description and search_term.lower() in t.description.lower()) or
                 (t.notes and search_term.lower() in t.notes.lower())]
    
    if project_filter:
        tasks = [t for t in tasks if t.project and project_filter.lower() in t.project.lower()]
    
    # Add list_title for grouping display
    if use_google_tasks:
        # For Google Tasks, tasks should already have list_title
        pass
    else:
        # For local mode, add default list_title if not already set
        for task in tasks:
            if not hasattr(task, 'list_title') or not task.list_title:
                # This shouldn't happen as task manager should have set it, but just in case
                task.list_title = list_filter if list_filter else "Tasks"
    
    return tasks


def handle_initial_search_command(task_manager, search_args, use_google_tasks):
    """Handle initial search command with arguments"""
    from gtasks_cli.models.task import TaskStatus
    
    if not search_args:
        return []
    
    # Remove quotes if present
    search_term = search_args.strip('"\'')
    
    # Get all tasks
    if use_google_tasks:
        tasks = task_manager.list_tasks()
    else:
        tasks = task_manager.list_tasks()
    
    # Filter tasks by search term
    filtered_tasks = []
    for task in tasks:
        # Check in title, description, and notes
        if (search_term.lower() in task.title.lower() or
            (task.description and search_term.lower() in task.description.lower()) or
            (task.notes and search_term.lower() in task.notes.lower())):
            filtered_tasks.append(task)
    
    # Add list_title for grouping display
    if use_google_tasks:
        # For Google Tasks, tasks should already have list_title
        pass
    else:
        # For local mode, add default list_title
        for task in filtered_tasks:
            # Check for both list_title and list_name attributes
            if not (hasattr(task, 'list_title') and task.list_title):
                if hasattr(task, 'list_name') and task.list_name:
                    task.list_title = task.list_name
                else:
                    task.list_title = "Tasks"
    
    return filtered_tasks