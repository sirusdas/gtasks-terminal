#!/usr/bin/env python3
"""
Interactive mode for Google Tasks CLI
"""

import click
import shlex
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.utils.datetime_utils import _normalize_datetime
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich import print as rich_print

# Initialize Rich console for colored output
console = Console()

logger = setup_logger(__name__)

# Try to import prompt_toolkit for better command line experience
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

# Import GoogleTasksClient for Google Tasks mode
try:
    from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
    HAS_GOOGLE_TASKS = True
except ImportError:
    HAS_GOOGLE_TASKS = False

# Import the help system
from gtasks_cli.commands.interactive_help import (
    show_general_help,
    show_view_help,
    show_done_help,
    show_delete_help,
    show_update_help,
    show_add_help,
    show_list_help,
    show_quit_help
)

# Import the time filter function
from gtasks_cli.commands.list import _filter_tasks_by_time


def _display_tasks_grouped_by_list(tasks, start_number=1):
    """Display tasks grouped by their list names"""
    # Group tasks by list title
    tasks_by_list = defaultdict(list)
    for task in tasks:
        list_title = getattr(task, 'list_title', 'Unknown List')
        tasks_by_list[list_title].append(task)
    
    # Display tasks grouped by list
    task_index = start_number
    all_tasks = []
    
    for list_title, list_tasks in tasks_by_list.items():
        # Display list name with color in a panel
        console.print(Panel(f"[bold blue]List Name: \"{list_title}\"[/bold blue]", expand=False))
        
        for i, task in enumerate(list_tasks, task_index):
            # For enum values, we need to check if they are already strings or enum instances
            status_value = task.status if isinstance(task.status, str) else task.status.value
            priority_value = task.priority if isinstance(task.priority, str) else task.priority.value
            
            # Color coding for status
            status_colors = {
                'pending': 'yellow',
                'in_progress': 'cyan',
                'completed': 'green',
                'waiting': 'magenta',
                'deleted': 'red'
            }
            status_icon = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'waiting': '⏸️',
                'deleted': '🗑️'
            }.get(status_value, '❓')
            status_color = status_colors.get(status_value, 'white')
            
            # Color coding for priority
            priority_colors = {
                'low': 'blue',
                'medium': 'yellow',
                'high': 'orange_red1',  # More vibrant orange
                'critical': 'red'
            }
            priority_icon = {
                'low': '🔽',
                'medium': '🔸',
                'high': '🔺',
                'critical': '💥'
            }.get(priority_value, '🔹')
            priority_color = priority_colors.get(priority_value, 'white')
            
            # Format due date if present
            due_info = ""
            if task.due:
                due_info = f" [blue]📅 {task.due.strftime('%Y-%m-%d')}[/blue]"
            
            # Format project if present
            project_info = ""
            if task.project:
                project_info = f" [purple]📁 {task.project}[/purple]"
            
            # Format tags if present
            tags_info = ""
            if task.tags:
                tags_info = f" [cyan]🏷️  {', '.join(task.tags)}[/cyan]"
            
            # Format recurring info
            recurring_info = ""
            if task.is_recurring:
                recurring_info = " [green]🔁[/green]"
            
            # Format description/notes with limit (max 3 lines)
            description_info = ""
            content = task.description or task.notes
            if content:
                # Limit content to 3 lines
                max_chars = 300
                desc = content.strip()
                if len(desc) > max_chars:
                    # Try to break at a word boundary
                    truncated = desc[:max_chars].rsplit(' ', 1)[0] + "..."
                    desc_lines = truncated.split('\n')
                else:
                    desc_lines = desc.split('\n')
                
                # Take only first 3 lines and format them
                formatted_lines = []
                for line in desc_lines[:3]:
                    if line.strip():  # Only add non-empty lines
                        formatted_lines.append(f"      [italic white]{line.strip()}[/italic white]")
                
                # Join the lines with newlines
                if formatted_lines:
                    description_info = "\n" + "\n".join(formatted_lines)
            
            # Display task with number
            task_line = f"  {i:2d}. [bright_black]{task.id[:8]}[/bright_black]: [{status_color}]{status_icon}[/{status_color}] [{priority_color}]{priority_icon}[/{priority_color}] {task.title}{due_info}{project_info}{tags_info}{recurring_info}{description_info}"
            console.print(task_line)
                
            all_tasks.append(task)
        task_index += len(list_tasks)
        console.print()  # Add spacing between lists
    
    return all_tasks


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
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'sqlite')
    logger.info(f"Starting interactive mode {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    from gtasks_cli.commands.list import task_state
    
    # Create task manager
    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend
    )
    
    # Get only pending/incomplete tasks by default
    if use_google_tasks:
        # For Google Tasks, we need to get tasks grouped by their lists
        from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
        client = GoogleTasksClient()
        tasklists = client.list_tasklists()
        
        tasks = []
        for tasklist in tasklists:
            tasklist_id = tasklist['id']
            tasklist_title = tasklist.get('title', 'Untitled List')
            # Get all tasks and filter for this specific tasklist
            all_tasks = task_manager.list_tasks()
            list_tasks = [t for t in all_tasks if getattr(t, 'tasklist_id', None) == tasklist_id]
            
            # Filter for incomplete tasks
            incomplete_tasks = [t for t in list_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
            
            # Add list_title to each task for grouping display
            for task in incomplete_tasks:
                task.list_title = tasklist_title
                
            tasks.extend(incomplete_tasks)
            
        # Display tasks grouped by list names with color coding
        _display_tasks_grouped_by_list(tasks)
        task_state.set_tasks(tasks)
    else:
        # For local mode, just get incomplete tasks
        tasks = task_manager.list_tasks()
        tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
        # Add list_title to each task for grouping display (default to "Tasks" for local mode)
        for task in tasks:
            if not hasattr(task, 'list_title') or not task.list_title:
                task.list_title = "Tasks"
        
        # Display tasks grouped by list names with color coding
        _display_tasks_grouped_by_list(tasks)
        task_state.set_tasks(tasks)
    
    if not tasks:
        click.echo("No incomplete tasks found.")
        return
    
    # Display tasks with numbers
    if use_google_tasks:
        # For Google Tasks, group by list names
        _display_tasks_grouped_by_list(tasks)
    else:
        # For local tasks, also group by list names
        _display_tasks_grouped_by_list(tasks)
    
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
                # Parse list command with filters
                list_filter = None
                status_filter = None
                priority_filter = None
                project_filter = None
                recurring_filter = False
                time_filter = None
                search_filter = None

                # Parse arguments
                i = 1
                while i < len(command_parts):
                    part = command_parts[i]
                    if part.startswith('--'):
                        if part == '--status' and i + 1 < len(command_parts):
                            status_filter = command_parts[i + 1]
                            i += 2
                        elif part == '--priority' and i + 1 < len(command_parts):
                            priority_filter = command_parts[i + 1]
                            i += 2
                        elif part == '--project' and i + 1 < len(command_parts):
                            project_filter = command_parts[i + 1]
                            i += 2
                        elif part in ['--recurring', '-r']:
                            recurring_filter = True
                            i += 1
                        elif part == '--filter' and i + 1 < len(command_parts):
                            time_filter = command_parts[i + 1]
                            i += 2
                        elif part == '--search' and i + 1 < len(command_parts):
                            search_filter = command_parts[i + 1]
                            i += 2
                        else:
                            i += 1
                    else:
                        # Positional argument (list filter)
                        list_filter = part
                        i += 1

                # Convert string filters to enum where needed
                status_enum = TaskStatus(status_filter) if status_filter else None
                priority_enum = Priority(priority_filter) if priority_filter else None

                if use_google_tasks:
                    from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
                    client = GoogleTasksClient()
                    tasklists = client.list_tasklists()

                    if list_filter:
                        tasklists = [tl for tl in tasklists if list_filter.lower() in tl.get('title', '').lower()]

                    if not tasklists:
                        click.echo("No matching task lists found.")
                        continue

                    # Display tasks grouped by list names
                    all_tasks = []
                    for tasklist in tasklists:
                        tasklist_id = tasklist['id']
                        tasklist_title = tasklist.get('title', 'Untitled List')
                        # Get tasks for this specific tasklist
                        tasks = task_manager.list_tasks()  # Get all tasks first
                        # Filter tasks by tasklist_id
                        tasks = [t for t in tasks if getattr(t, 'tasklist_id', None) == tasklist_id]
                        
                        # Apply status filter or default to incomplete tasks
                        if status_enum:
                            tasks = [t for t in tasks if t.status == status_enum]
                        else:
                            # Default to incomplete tasks
                            tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
                                            
                        # Add list_title to each task for grouping display
                        for task in tasks:
                            if not hasattr(task, 'list_title') or not task.list_title:
                                task.list_title = tasklist_title
                            
                        # Apply additional filters
                        if priority_enum:
                            tasks = [t for t in tasks if t.priority == priority_enum]
                            
                        if project_filter:
                            tasks = [t for t in tasks if t.project == project_filter]

                        if recurring_filter:
                            tasks = [t for t in tasks if t.is_recurring]

                        if time_filter:
                            tasks = _filter_tasks_by_time(tasks, time_filter)

                        if search_filter:
                            tasks = [t for t in tasks if search_filter.lower() in t.title.lower() or 
                                    (t.description and search_filter.lower() in t.description.lower())]
                        # Add list_title to each task for grouping display
                        for task in tasks:
                            if not hasattr(task, 'list_title') or not task.list_title:
                                task.list_title = tasklist_title
                        
                        all_tasks.extend(tasks)
                    
                    # Display tasks grouped by list names
                    displayed_tasks = _display_tasks_grouped_by_list(all_tasks)
                    task_state.tasks = displayed_tasks
                else:
                    # Local mode with list filtering support
                    all_tasks = task_manager.list_tasks(
                        list_filter=list_filter,
                        status=status_enum,
                        priority=priority_enum,
                        project=project_filter,
                        recurring=recurring_filter
                    )
                    
                    # Apply time filter if provided
                    if time_filter:
                        all_tasks = _filter_tasks_by_time(all_tasks, time_filter)
                    
                    # Apply search filter if provided
                    if search_filter:
                        all_tasks = [t for t in all_tasks if search_filter.lower() in t.title.lower() or 
                                   (t.description and search_filter.lower() in t.description.lower()) or
                                   (t.notes and search_filter.lower() in t.notes.lower())]
                    
                    # Add list_title to each task for grouping display (default to "Tasks" for local mode)
                    for task in all_tasks:
                        if not hasattr(task, 'list_title') or not task.list_title:
                            task.list_title = "Tasks"
                    
                    # Display tasks grouped by list names with color coding
                    displayed_tasks = _display_tasks_grouped_by_list(all_tasks)
                    task_state.set_tasks(displayed_tasks)
            elif cmd == 'view':
                if len(command_parts) < 2:
                    click.echo("Usage: view <number>")
                    continue
                    
                try:
                    task_num = int(command_parts[1])
                    task = task_state.get_task_by_number(task_num)
                    if task:
                        _view_task_details(task)
                    else:
                        click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.tasks)}.")
                except ValueError:
                    click.echo("Invalid task number. Please enter a valid integer.")
            elif cmd == 'done':
                if len(command_parts) < 2:
                    click.echo("Usage: done <number>")
                    continue
                    
                try:
                    task_num = int(command_parts[1])
                    task = task_state.get_task_by_number(task_num)
                    if task:
                        if task_manager.complete_task(task.id):
                            click.echo(f"Task '{task.title}' marked as completed.")
                            # Refresh task list - only show incomplete tasks
                            tasks = task_manager.list_tasks()
                            incomplete_tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
                            # Add list_title to each task for grouping display (default to "Tasks" for local mode)
                            for task in incomplete_tasks:
                                if not hasattr(task, 'list_title') or not task.list_title:
                                    task.list_title = "Tasks"
                            _display_tasks_grouped_by_list(incomplete_tasks)
                            task_state.set_tasks(incomplete_tasks)
                        else:
                            click.echo("Failed to mark task as completed.")
                    else:
                        click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.tasks)}.")
                except ValueError:
                    click.echo("Invalid task number. Please enter a valid integer.")
            elif cmd == 'delete':
                if len(command_parts) < 2:
                    click.echo("Usage: delete <task_number>")
                    continue
                    
                try:
                    task_num = int(command_parts[1])
                    task = task_state.get_task_by_number(task_num)
                    if task:
                        confirm = click.confirm(f"Are you sure you want to delete task '{task.title}'?")
                        if confirm:
                            if task_manager.delete_task(task.id):
                                click.echo(f"Task '{task.title}' deleted.")
                                # Refresh task list - only show incomplete tasks
                                if use_google_tasks:
                                    # For Google Tasks, we need to get tasks grouped by their lists
                                    client = GoogleTasksClient()
                                    tasklists = client.list_tasklists()
                                    
                                    tasks = []
                                    for tasklist in tasklists:
                                        tasklist_id = tasklist['id']
                                        tasklist_title = tasklist.get('title', 'Untitled List')
                                        # Get all tasks and filter for this specific tasklist
                                        all_tasks = task_manager.list_tasks()
                                        list_tasks = [t for t in all_tasks if getattr(t, 'tasklist_id', None) == tasklist_id]
                                        
                                        # Filter for incomplete tasks
                                        incomplete_tasks = [t for t in list_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
                                        
                                        # Add list_title to each task for grouping display
                                        for task_item in incomplete_tasks:
                                            task_item.list_title = tasklist_title
                                            
                                        tasks.extend(incomplete_tasks)
                                    
                                    _display_tasks_grouped_by_list(tasks)
                                    task_state.set_tasks(tasks)
                                else:
                                    # For local mode
                                    tasks = task_manager.list_tasks()
                                    incomplete_tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
                                    _display_numbered_tasks(incomplete_tasks)
                                    task_state.set_tasks(incomplete_tasks)
                            else:
                                click.echo("Failed to delete task.")
                    else:
                        click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.tasks)}.")
                except ValueError:
                    click.echo("Invalid task number. Please enter a valid integer.")
            elif cmd == 'add':
                # Collect task details
                title = click.prompt("Task title")
                description = click.prompt("Task description", default="")
                if description == "":
                    description = None
                
                # Get available task lists
                tasklist_name = None
                tasklist_id = None
                
                if use_google_tasks:
                    # For Google Tasks, get available task lists
                    try:
                        client = GoogleTasksClient()
                        tasklists = client.list_tasklists()
                        if tasklists:
                            click.echo("\nAvailable task lists:")
                            for i, tasklist in enumerate(tasklists, 1):
                                click.echo(f"  {i}. {tasklist.get('title', 'Untitled List')}")
                            
                            # Ask user to select a task list
                            while True:
                                try:
                                    choice = click.prompt("Select task list (number)", type=int)
                                    if 1 <= choice <= len(tasklists):
                                        selected_tasklist = tasklists[choice - 1]
                                        tasklist_name = selected_tasklist.get('title')
                                        tasklist_id = selected_tasklist.get('id')
                                        break
                                    else:
                                        click.echo(f"Please enter a number between 1 and {len(tasklists)}")
                                except (ValueError, click.Abort):
                                    click.echo("Invalid input. Please enter a valid number.")
                        else:
                            click.echo("No task lists found. Using default list.")
                    except Exception as e:
                        logger.error(f"Error getting task lists: {e}")
                        click.echo("Error retrieving task lists. Using default list.")
                else:
                    # For local mode, get list names from storage or offer defaults
                    try:
                        list_names = task_manager.get_list_names()
                        if not list_names:
                            # If no lists exist, provide some defaults
                            list_names = ["Tasks", "Work", "Personal", "Shopping", "Projects"]
                    except Exception as e:
                        logger.error(f"Error getting list names: {e}")
                        # Fallback to defaults
                        list_names = ["Tasks", "Work", "Personal", "Shopping", "Projects"]
                    
                    click.echo("\nAvailable task lists:")
                    for i, list_name in enumerate(list_names, 1):
                        click.echo(f"  {i}. {list_name}")
                    click.echo(f"  {len(list_names) + 1}. Enter custom list name")
                    
                    while True:
                        try:
                            choice = click.prompt("Select task list (number)", type=int)
                            if 1 <= choice <= len(list_names):
                                tasklist_name = list_names[choice - 1]
                                break
                            elif choice == len(list_names) + 1:
                                tasklist_name = click.prompt("Enter custom task list name")
                                break
                            else:
                                click.echo(f"Please enter a number between 1 and {len(list_names) + 1}")
                        except (ValueError, click.Abort):
                            click.echo("Invalid input. Please enter a valid number.")
                
                # Add the task using the correct method name
                task = task_manager.create_task(
                    title=title, 
                    description=description,
                    tasklist_name=tasklist_name,
                    tasklist_id=tasklist_id
                )
                if task:
                    click.echo(f"Task '{title}' added successfully.")
                    # Refresh task list - only show incomplete tasks and maintain grouped display
                    tasks = task_manager.list_tasks()
                    incomplete_tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]

                    # Add list_title to each task for grouping display (default to "Tasks" for local mode)
                    for task in incomplete_tasks:
                        if not hasattr(task, 'list_title') or not task.list_title:
                            task.list_title = "Tasks"

                    # Display tasks grouped by list names
                    displayed_tasks = _display_tasks_grouped_by_list(incomplete_tasks)
                    task_state.set_tasks(displayed_tasks)
                else:
                    click.echo("Failed to add task.")
            elif cmd == 'update':
                if len(command_parts) < 2:
                    click.echo("Usage: update <task_number>")
                    continue
                    
                try:
                    task_num = int(command_parts[1])
                    task = task_state.get_task_by_number(task_num)
                    if task:
                        # Collect updated details
                        title = click.prompt("Task title", default=task.title)
                        description = click.prompt("Task description", default=task.description or "")
                        if description == "":
                            description = None
                        
                        # Update the task
                        updated_task = task_manager.update_task(task.id, title=title, description=description)
                        if updated_task:
                            click.echo(f"Task '{title}' updated successfully.")
                            # Refresh task list - only show incomplete tasks
                            tasks = task_manager.list_tasks()
                            incomplete_tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]

                            # Add list_title to each task for grouping display (default to "Tasks" for local mode)
                            for task in incomplete_tasks:
                                if not hasattr(task, 'list_title') or not task.list_title:
                                    task.list_title = "Tasks"

                            _display_tasks_grouped_by_list(incomplete_tasks)
                            task_state.set_tasks(incomplete_tasks)
                        else:
                            click.echo("Failed to update task.")
                    else:
                        click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.tasks)}.")
                except ValueError:
                    click.echo("Invalid task number. Please enter a valid integer.")
            elif cmd == 'search':
                if len(command_parts) < 2:
                    click.echo("Usage: search <query>")
                    continue
                    
                query = " ".join(command_parts[1:])
                # Use list_tasks with search parameter instead of non-existent search_tasks method
                search_results = task_manager.list_tasks(search=query)
                if search_results:
                    click.echo(f"\nSearch results for '{query}':")
                    _display_tasks_grouped_by_list(search_results)
                    task_state.set_tasks(search_results)
                else:
                    click.echo(f"No tasks found matching '{query}'.")
                    # Keep current tasks unchanged
            elif cmd == 'help':
                if len(command_parts) > 1:
                    subcommand = command_parts[1]
                    if subcommand == 'search':
                        # Display detailed help for search command with colors
                        console.print(Panel("[bold blue]Search Command Help[/bold blue]", expand=False))
                        
                        console.print("[bold]Description:[/bold]")
                        console.print("Search for tasks by providing terms that will be matched against task titles,")
                        console.print("descriptions, and notes. Use the pipe character (|) to search for multiple")
                        console.print("terms with OR logic.\n")
                        
                        console.print("[bold]Usage:[/bold]")
                        console.print("  search <query>\n")
                        
                        console.print("[bold]Examples:[/bold]")
                        console.print("  [green]# Search for tasks containing \"meeting\"[/green]")
                        console.print("  search meeting\n")
                        
                        console.print("  [green]# Search for tasks containing \"meeting\", \"project\", OR \"review\"[/green]")
                        console.print("  search \"meeting|project|review\"\n")
                        
                        console.print("  [green]# Search in combination with other commands[/green]")
                        console.print("  list --search \"meeting\" --status pending")
                        console.print("  list --search \"report|presentation\" --priority high\n")
                        
                        console.print("[bold]Multi-Search:[/bold]")
                        console.print("Use the pipe character (|) to search for multiple terms:")
                        console.print("  search \"term1|term2|term3\"")
                        console.print("This will return tasks matching [bold]any[/bold] of the provided terms.\n")
                        
                        console.print("[bold]Filter Options:[/bold]")
                        console.print("You can combine search with other filters:")
                        console.print("  [yellow]--status[/yellow]     Filter by status (pending, in_progress, completed, waiting, deleted)")
                        console.print("  [yellow]--priority[/yellow]   Filter by priority (low, medium, high, critical)")
                        console.print("  [yellow]--project[/yellow]    Filter by project")
                        console.print("  [yellow]--recurring[/yellow]  Show only recurring tasks\n")
                        
                        console.print("[bold]Interactive Mode Usage:[/bold]")
                        console.print("In interactive mode, simply type:")
                        console.print("  search <query>")
                        console.print("The results will be displayed and can be operated on using other commands.\n")
                    elif subcommand == 'view':
                        show_view_help()
                    elif subcommand == 'done':
                        show_done_help()
                    elif subcommand == 'delete':
                        show_delete_help()
                    elif subcommand == 'update':
                        show_update_help()
                    elif subcommand == 'add':
                        show_add_help()
                    elif subcommand == 'list':
                        show_list_help()
                    elif subcommand in ['quit', 'exit']:
                        show_quit_help()
                    else:
                        click.echo(f"Unknown command: {subcommand}. Type 'help' for available commands.")
                else:
                    show_general_help()
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




def _display_tasks(tasks, start_number=1):
    """Display tasks with numbering"""
    tasks_header = Text("\nTasks:", style="bold green")
    console.print(tasks_header)
    for i, task in enumerate(tasks, start_number):
        _display_single_task(i, task)


# Remove _display_single_task as it's no longer needed
# The functionality is now handled by _display_tasks_grouped_by_list


# Remove _display_numbered_tasks as it's no longer needed
# The functionality is now handled by _display_tasks_grouped_by_list


def _view_task_details(task):
    """Display detailed information about a task with color formatting"""
    # Create a panel for the task details
    panel_content = []
    
    # Add basic task info
    panel_content.append(f"[bold]{task.title}[/bold]")
    panel_content.append(f"ID: {task.id}")
    
    # Add description
    if task.description:
        # Format description with proper alignment and limit
        max_chars = 500  # Increased limit for view details
        desc = task.description.strip()
        if len(desc) > max_chars:
            desc = desc[:max_chars].rsplit(' ', 1)[0] + "..."
        
        # Split description into lines for proper alignment
        desc_lines = desc.split('\n')
        formatted_desc = "\n".join([f"    {line}" for line in desc_lines])
        panel_content.append(f"[italic white]📝 {formatted_desc}[/italic white]")
    
    # Add notes
    if task.notes:
        panel_content.append(f"📌 Notes: {task.notes}")
    
    # Add due date
    if task.due:
        panel_content.append(f"[blue]📅 Due: {task.due.strftime('%Y-%m-%d')}[/blue]")
    
    # Add status and priority on the same line
    status_value = task.status if isinstance(task.status, str) else task.status.value
    status_colors = {
        'pending': 'yellow',
        'in_progress': 'cyan',
        'completed': 'green',
        'waiting': 'magenta',
        'deleted': 'red'
    }
    status_icon = {
        'pending': '⏳',
        'in_progress': '🔄',
        'completed': '✅',
        'waiting': '⏸️',
        'deleted': '🗑️'
    }.get(status_value, '❓')
    status_color = status_colors.get(status_value, 'white')
    
    priority_value = task.priority if isinstance(task.priority, str) else task.priority.value
    priority_colors = {
        'low': 'blue',
        'medium': 'yellow',
        'high': 'orange_red1',
        'critical': 'red'
    }
    priority_icon = {
        'low': '🔽',
        'medium': '🔸',
        'high': '🔺',
        'critical': '💥'
    }.get(priority_value, '🔹')
    priority_color = priority_colors.get(priority_value, 'white')
    
    status_priority_line = f"[{status_color}]{status_icon} {status_value.upper()}[/{status_color}] | [{priority_color}]{priority_icon} {priority_value.upper()}[/{priority_color}]"
    panel_content.append(status_priority_line)
    
    # Add project and tags
    project_tags_line = ""
    if task.project:
        project_tags_line += f"📁 {task.project}  "
    if task.tags:
        project_tags_line += f"🏷️  {', '.join(task.tags)}"
    
    if project_tags_line:
        panel_content.append(project_tags_line)
    
    # Add recurrence info
    if task.is_recurring:
        panel_content.append("🔁 Recurring Task")
    
    # Add dependencies
    if task.dependencies:
        deps_formatted = ", ".join(task.dependencies)
        panel_content.append(f"🔗 Dependencies: {deps_formatted}")
    
    # Add timestamps
    timestamp_lines = []
    timestamp_lines.append(f"⏱️ Created: {task.created_at}")
    if task.modified_at:
        timestamp_lines.append(f"🔄 Modified: {task.modified_at}")
    if hasattr(task, 'completed_at') and task.completed_at:
        timestamp_lines.append(f"✅ Completed: {task.completed_at}")
    
    if timestamp_lines:
        panel_content.extend(timestamp_lines)
    
    # Create and print the panel
    panel = Panel("\n".join(panel_content), title="Task Details", expand=False, border_style="bright_black")
    console.print(panel)