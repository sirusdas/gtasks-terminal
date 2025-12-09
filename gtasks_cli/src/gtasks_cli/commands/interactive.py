#!/usr/bin/env python3
"""
Interactive mode for Google Tasks CLI
"""

import click
import shlex
import tempfile
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.commands.interactive_utils.initial_commands import handle_initial_list_command, handle_initial_search_command
from gtasks_cli.commands.interactive_utils.display import display_tasks_grouped_by_list
from gtasks_cli.commands.interactive_utils.task_details import view_task_details
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
    from prompt_toolkit.history import FileHistory, InMemoryHistory
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
    show_bulk_update_help,
    show_tags_help
)

# Import time filtering function
from gtasks_cli.commands.list import _filter_tasks_by_time, _sort_tasks

# State for interactive mode
class TaskState:
    """Hold state for interactive mode"""
    def __init__(self):
        self.tasks = []
        self.task_number_to_id = {}
        self.task_id_to_number = {}
        # Track the current command context for navigation
        self.command_history = []  # Stack of commands for 'back' functionality
        self.default_tasks = []    # Default task list for 'default' functionality
    
    def set_tasks(self, tasks: List[Task], is_default=False):
        """Set tasks and create mappings"""
        self.tasks = tasks
        self.task_number_to_id = {}
        self.task_id_to_number = {}
        
        for i, task in enumerate(tasks, 1):
            self.task_number_to_id[i] = task.id
            self.task_id_to_number[task.id] = i
            
            
        if is_default:
            self.default_tasks = tasks.copy()
    
    def push_command(self, command: str):
        """Push a command to the history stack"""
        self.command_history.append(command)
    
    def pop_command(self):
        """Pop and return the last command from history, or None if empty"""
        if self.command_history:
            return self.command_history.pop()
        return None
    
    def get_default_tasks(self):
        """Get the default task list"""
        return self.default_tasks
    
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


def _display_tasks_grouped_by_list(tasks: List[Task]) -> List[Task]:
    """Display tasks grouped by their task lists with color coding.
    Returns the displayed tasks for state tracking."""
    if not tasks:
        click.echo("No tasks found.")
        return tasks
    
    # Group tasks by list
    tasks_by_list = defaultdict(list)
    for task in tasks:
        list_title = getattr(task, 'list_title', 'Tasks')
        tasks_by_list[list_title].append(task)
    
    # Display tasks grouped by list
    for list_title, list_tasks in tasks_by_list.items():
        # Use different colors for different lists
        list_title_color = 'blue'
        if 'work' in list_title.lower():
            list_title_color = 'cyan'
        elif 'personal' in list_title.lower():
            list_title_color = 'green'
        elif 'shopping' in list_title.lower():
            list_title_color = 'yellow'
        
        console.print(Panel(f"[bold]{list_title}[/bold]", expand=False, style=list_title_color))
        
        for i, task in enumerate(list_tasks, 1):
            # Find the global index of this task
            global_index = next((j for j, t in enumerate(tasks, 1) if t.id == task.id), i)
            
            # Format the task line with priority indicator
            priority_icons = {
                'LOW': '🔽',
                'MEDIUM': '🔸', 
                'HIGH': '🔺',
                'CRITICAL': '💥'
            }
            priority_icon = priority_icons.get(str(task.priority).upper(), '🔸')
            
            # Format due date
            due_str = ""
            if task.due:
                try:
                    if isinstance(task.due, str):
                        due_date = datetime.fromisoformat(task.due)
                    else:
                        due_date = task.due
                    
                    # Normalize datetime to remove timezone for comparison
                    due_date = due_date.replace(tzinfo=None)
                    now = datetime.now().replace(tzinfo=None)
                    
                    # Format based on proximity to current date
                    if due_date.date() == now.date():
                        due_str = " 📅 Today"
                    elif due_date.date() == (now + timedelta(days=1)).date():
                        due_str = " 📅 Tomorrow"
                    elif due_date.date() < now.date():
                        due_str = " ⏳ Overdue"
                    else:
                        due_str = f" 📅 {due_date.strftime('%Y-%m-%d')}"
                except Exception as e:
                    logger.debug(f"Error formatting due date: {e}")
                    due_str = ""
            
            # Format created, modified, and due dates
            dates_str = ""
            if task.due:
                due_date_str = task.due.strftime('%Y-%m-%d') if hasattr(task.due, 'strftime') else str(task.due)[:10]
                dates_str += f" [dim]D:{due_date_str}[/dim]"
            
            if task.created_at:
                dates_str += f" [dim]C:{task.created_at.strftime('%Y-%m-%d')}[/dim]"
            if task.modified_at:
                dates_str += f" [dim]M:{task.modified_at.strftime('%Y-%m-%d')}[/dim]"
            
            # Build the task line
            task_line = f"{global_index:2d}. {priority_icon} {task.title}{due_str}{dates_str}"
            
            # Color code task status
            status_colors = {
                'PENDING': 'white',
                'IN_PROGRESS': 'cyan',
                'COMPLETED': 'green',
                'WAITING': 'yellow',
                'DELETED': 'red'
            }
            task_color = status_colors.get(str(task.status).upper(), 'white')
            
            console.print(task_line, style=task_color)
            
            # Display description if available
            if task.description:
                # Truncate long descriptions
                desc = task.description[:60] + "..." if len(task.description) > 60 else task.description
                console.print(f"     📝 {desc}")
                
            # Display notes if available
            if task.notes is not None:
                notes_stripped = task.notes.strip()
                if notes_stripped:
                    # Split notes into lines
                    note_lines = notes_stripped.splitlines()
                    # Show at least 3 lines or up to 200 characters
                    displayed_lines = note_lines[:3]  # Take up to 3 lines
                    notes = "\n     📓 ".join(displayed_lines)  # Join with prefix for each line
                    
                    # If we have more than 200 characters, truncate and add ellipsis
                    if len(notes) > 200:
                        notes = notes[:200] + "..."
                    
                    # Using Rich console print with proper text handling
                    note_text = Text(f"     📓 {notes}")
                    console.print(note_text)
    
    # Summary
    console.print(f"\nTotal: {len(tasks)} task(s) across {len(tasks_by_list)} list(s)")
    
    return tasks


def show_quit_help():
    """Show help for the quit/exit command"""
    console.print(Panel("[bold blue]Quit/Exit Command Help[/bold blue]", expand=False))
    
    console.print("[bold]Description:[/bold]")
    console.print("Exit the interactive mode and return to the command line.\n")
    
    console.print("[bold]Usage:[/bold]")
    console.print("  quit")
    console.print("  exit\n")
    
    console.print("[bold]Example:[/bold]")
    console.print("  quit")
    console.print("  This will exit the interactive mode.")


@click.command()
@click.argument('command', nargs=-1)
@click.pass_context
def interactive(ctx, command):
    """Start interactive mode for task management.
    
    In interactive mode, tasks are numbered sequentially and you can perform
    operations on them using these numbers.
    
    You can also pass a command directly to start with a filtered list:
    
    \b
    Examples:
      gtasks interactive -- list --status pending --filter this_week
      gtasks interactive -- search "important project"
      gtasks interactive -- tags
      gtasks interactive -- list --list-names
    
    \b
    Commands in interactive mode:
      view <number>           - View task details
      done <number>           - Mark task as completed
      delete <number>         - Delete a task
      update <number>         - Update a task
      update-status <spec>    - Bulk update task status and due dates
      update-tags <spec>      - Bulk update task tags
      undo                    - Undo the last operation
      add                     - Add a new task
      list                    - List all tasks
      list [filter]           - List tasks with filters (same as gtasks list command)
      search <query>          - Search tasks
      tags                    - Filter tasks by tags
      list --list-names       - Filter tasks by list names
      back                    - Go back to previous command results
      default                 - Go back to default listing
      help                    - Show this help
      quit/exit               - Exit interactive mode
    """
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'sqlite')
    account_name = ctx.obj.get('account_name', None)
    cli_auto_save = ctx.obj.get('auto_save', None)
    logger.info(f"Starting interactive mode {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    from gtasks_cli.commands.list import task_state as list_task_state
    
    # Create task manager
    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend,
        account_name=account_name
    )
    
    # Store CLI auto-save option in task_manager for access by interactive utils
    task_manager.cli_auto_save = cli_auto_save
    
    # Parse initial command if provided
    initial_command = None
    if command:
        initial_command = ' '.join(command)
        logger.debug(f"Initial command provided: {initial_command}")
    
    # Get tasks based on initial command or default to incomplete tasks
    tasks = []
    if initial_command:
        # Parse the initial command
        if initial_command.startswith('list'):
            # Handle list command with filters
            list_args = initial_command[4:].strip()  # Remove 'list' and get the rest
            # Check if this is the special list --list-names command
            if '--list-names' in list_args:
                # Handle list names selection
                from gtasks_cli.commands.interactive_utils.list_commands import handle_list_filtering_interactive_mode
                handle_list_filtering_interactive_mode(task_manager, use_google_tasks)
                return  # Exit after list filtering interactive mode
            else:
                tasks = handle_initial_list_command(task_manager, list_args, use_google_tasks)
        elif initial_command.startswith('search'):
            # Handle search command
            search_args = initial_command[6:].strip()  # Remove 'search' and get the rest
            tasks = handle_initial_search_command(task_manager, search_args, use_google_tasks)
        elif initial_command.startswith('tags'):
            # Handle tags command
            from gtasks_cli.commands.interactive_utils.tag_commands import handle_tag_filtering_interactive_mode
            handle_tag_filtering_interactive_mode(task_manager, use_google_tasks)
            return  # Exit after tag filtering interactive mode
        else:
            # Invalid initial command
            click.echo(f"Invalid initial command: {initial_command}")
            click.echo("Supported initial commands: list, search, tags")
            return
    else:
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
        else:
            # For local mode, just get incomplete tasks
            tasks = task_manager.list_tasks()
            logger.debug(f"Loaded {len(tasks)} total tasks")
            for task in tasks:
                logger.debug(f"Task: {task.title} (ID: {task.id}) - Status: {task.status}")
            tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
            logger.debug(f"Filtered to {len(tasks)} incomplete tasks")
            # Add list_title to each task for grouping display (default to "Tasks" for local mode)
            for task in tasks:
                if not hasattr(task, 'list_title') or not task.list_title:
                    task.list_title = "Tasks"
    
    if not tasks:
        # Check if we had initial command filters
        if initial_command:
            click.echo("No tasks found matching your criteria.")
        else:
            click.echo("No incomplete tasks found.")
        return
    
    # Display tasks with numbers
    _display_tasks_grouped_by_list(tasks)
    
    # Store current tasks in task_state
    task_state.set_tasks(tasks, is_default=(not initial_command))
    if initial_command:
        task_state.push_command(initial_command)
    
    # Command history for prompt_toolkit
    if HAS_PROMPT_TOOLKIT:
        history_file = os.path.expanduser("~/.gtasks_history")
        try:
            history = FileHistory(history_file)
        except Exception as e:
            logger.warning(f"Could not create history file at {history_file}: {e}. Using in-memory history.")
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
            
            # Check if this is a piped command (contains | outside of square brackets)
            # We need to distinguish between command pipes like "search foo | view"
            # and syntax pipes like "update-tags ADD[1|tag]"
            def has_command_pipe(cmd: str) -> bool:
                """Check if command has a pipe outside of square brackets."""
                depth = 0
                for char in cmd:
                    if char == '[':
                        depth += 1
                    elif char == ']':
                        depth -= 1
                    elif char == '|' and depth == 0:
                        return True
                return False
            
            if has_command_pipe(command_input):
                from gtasks_cli.commands.interactive_utils.piped_commands import handle_piped_command
                if handle_piped_command(command_input, task_state, task_manager, use_google_tasks):
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
            elif cmd == 'back':
                # Go back to previous command results
                previous_command = task_state.pop_command()
                if previous_command:
                    # Re-execute the previous command
                    if previous_command.startswith('list'):
                        # Check if this is the special list --list-names command
                        if '--list-names' in previous_command:
                            from gtasks_cli.commands.interactive_utils.list_commands import handle_list_filtering_interactive_mode
                            handle_list_filtering_interactive_mode(task_manager, use_google_tasks)
                            # After list filtering mode, we need to refresh the task display
                            _display_tasks_grouped_by_list(task_state.tasks)
                        else:
                            list_args = previous_command[4:].strip()
                            tasks = handle_initial_list_command(task_manager, list_args, use_google_tasks)
                            _display_tasks_grouped_by_list(tasks)
                            task_state.set_tasks(tasks)
                            task_state.push_command(previous_command)
                    elif previous_command.startswith('search'):
                        search_args = previous_command[6:].strip()
                        tasks = handle_initial_search_command(task_manager, search_args, use_google_tasks)
                        _display_tasks_grouped_by_list(tasks)
                        task_state.set_tasks(tasks)
                        task_state.push_command(previous_command)
                    elif previous_command.startswith('tags'):
                        from gtasks_cli.commands.interactive_utils.tag_commands import handle_tag_filtering_interactive_mode
                        handle_tag_filtering_interactive_mode(task_manager, use_google_tasks)
                        # After tag filtering mode, we need to refresh the task display
                        _display_tasks_grouped_by_list(task_state.tasks)
                    else:
                        # For other commands, go back to default view
                        tasks = task_state.get_default_tasks()
                        _display_tasks_grouped_by_list(tasks)
                        task_state.set_tasks(tasks)
                else:
                    # No previous command, go to default view
                    tasks = task_state.get_default_tasks()
                    _display_tasks_grouped_by_list(tasks)
                    task_state.set_tasks(tasks, is_default=True)
            elif cmd == 'default':
                # Go back to default listing
                tasks = task_state.get_default_tasks()
                if tasks:
                    _display_tasks_grouped_by_list(tasks)
                    task_state.set_tasks(tasks, is_default=True)
                    # Clear command history when going to default
                    task_state.command_history.clear()
                else:
                    click.echo("No default task list available.")
            elif cmd == 'list':
                # Parse list command with filters
                list_filter = None
                status_filter = None
                priority_filter = None
                project_filter = None
                recurring_filter = False
                time_filter = None
                search_filter = None
                order_by = None
                tags_filter = None
                list_names_flag = False  # Flag for --list-names option

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
                        elif part in ['--order-by', '-o'] and i + 1 < len(command_parts):
                            order_by = command_parts[i + 1]
                            i += 2
                        elif part == '--search' and i + 1 < len(command_parts):
                            search_filter = command_parts[i + 1]
                            i += 2
                        elif part == '--list-names':
                            list_names_flag = True
                            i += 1
                        elif part in ['--tags', '-t'] and i + 1 < len(command_parts):
                            tags_filter = command_parts[i + 1]
                            i += 2
                        else:
                            i += 1
                    else:
                        # Positional argument (list filter)
                        list_filter = part
                        i += 1
                
                # Handle the special case of list --list-names
                if list_names_flag:
                    from gtasks_cli.commands.interactive_utils.list_commands import handle_list_filtering_interactive_mode
                    handle_list_filtering_interactive_mode(task_manager, use_google_tasks)
                    # After list filtering mode, we need to refresh the task display
                    _display_tasks_grouped_by_list(task_state.tasks)
                    task_state.push_command(command_input)
                    continue

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
                           from gtasks_cli.commands.interactive_utils.search import apply_search_filter
                           tasks = [t for t in tasks if t.is_recurring]

                        if time_filter:
                            tasks = _filter_tasks_by_time(tasks, time_filter)

                        if search_filter:
                            tasks = apply_search_filter(tasks, search_filter)
                        
                        if tags_filter:
                            from gtasks_cli.commands.interactive_utils.search import apply_tag_filter
                            tasks = apply_tag_filter(tasks, tags_filter)
                        
                        # Add list_title to each task for grouping display
                        for task in tasks:
                            if not hasattr(task, 'list_title') or not task.list_title:
                                task.list_title = tasklist_title
                        
                        all_tasks.extend(tasks)
                    
                    # Display tasks grouped by list names
                    displayed_tasks = display_tasks_grouped_by_list(all_tasks)
                    task_state.set_tasks(displayed_tasks)
                    task_state.push_command(command_input)
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
                        # Support enhanced search with exclusion and exact matching
                        all_tasks = apply_search_filter(all_tasks, search_filter)
                    
                    # Apply tags filter if provided
                    if tags_filter:
                        from gtasks_cli.commands.interactive_utils.search import apply_tag_filter
                        all_tasks = apply_tag_filter(all_tasks, tags_filter)

                    # Apply sorting if requested
                    if order_by:
                        from gtasks_cli.commands.list import _sort_tasks
                        all_tasks = _sort_tasks(all_tasks, order_by)
                    
                    # Add list_title to each task for grouping display (default to "Tasks" for local mode)
                    for task in all_tasks:
                        if not hasattr(task, 'list_title') or not task.list_title:
                            task.list_title = "Tasks"
                    
                    # Display tasks grouped by list names with color coding
                    displayed_tasks = _display_tasks_grouped_by_list(all_tasks)
                    task_state.set_tasks(displayed_tasks)
                    task_state.push_command(command_input)
            elif cmd == 'view':
                if len(command_parts) < 2:
                    click.echo("Usage: view <number>[,<number>,...] or view all")
                    continue

                # Handle "view all" command
                if command_parts[1].lower() == 'all':
                    # View all tasks in the current result set
                    if not task_state.tasks:
                        click.echo("No tasks to display.")
                        continue

                    for i, task in enumerate(task_state.tasks, 1):
                        console.print(f"\n[bold underline]Task #{i} of {len(task_state.tasks)}:[/bold underline]")
                        _view_task_details(task)
                    continue

                # Handle multiple task IDs
                task_numbers_str = command_parts[1]
                task_numbers = []

                # Parse comma-separated task numbers
                try:
                    task_numbers = [int(num.strip()) for num in task_numbers_str.split(',') if num.strip()]
                except ValueError:
                    click.echo("Invalid task number(s). Please enter valid integers separated by commas, or 'all' to view all tasks.")
                    continue

                if not task_numbers:
                    click.echo("No valid task numbers provided.")
                    continue

                # Validate task numbers
                invalid_numbers = [num for num in task_numbers if not task_state.get_task_by_number(num)]
                if invalid_numbers:
                    click.echo(f"Invalid task number(s): {', '.join(map(str, invalid_numbers))}. Please enter numbers between 1 and {len(task_state.tasks)}.")
                    continue

                # View each requested task
                for task_num in task_numbers:
                    task = task_state.get_task_by_number(task_num)
                    if task:
                        console.print(f"\n[bold underline]Task #{task_num}:[/bold underline]")
                        _view_task_details(task)
            elif cmd == 'add':
                # Import and use the add command handler
                from gtasks_cli.commands.interactive_utils.add_commands import handle_add_command
                handle_add_command(task_state, task_manager, command_parts, use_google_tasks)
            elif cmd == 'done':
                # Import and use the done command handler
                from gtasks_cli.commands.interactive_utils.done_commands import handle_done_command
                handle_done_command(task_state, task_manager, command_parts, use_google_tasks)
            elif cmd == 'delete':
                # Import and use the delete command handler
                from gtasks_cli.commands.interactive_utils.delete_commands import handle_delete_command
                handle_delete_command(task_state, task_manager, command_parts, use_google_tasks)
            elif cmd == 'update':
                # Import and use the update command handler
                from gtasks_cli.commands.interactive_utils.update_commands import handle_update_command
                handle_update_command(task_state, task_manager, command_parts, use_google_tasks)
            elif cmd == 'update-status':
                # Import and use the bulk update command handler
                from gtasks_cli.commands.interactive_utils.bulk_update_commands import handle_bulk_update_command
                handle_bulk_update_command(task_state, task_manager, command_parts, use_google_tasks)
            elif cmd == 'update-tags':
                # Import and use the update tags command handler
                from gtasks_cli.commands.interactive_utils.update_tags_commands import handle_update_tags_command
                handle_update_tags_command(task_state, task_manager, command_parts, use_google_tasks)
            elif cmd == 'undo':
                from gtasks_cli.commands.interactive_utils.undo_manager import undo_manager
                op = undo_manager.pop_undo()
                if op:
                    click.echo(f"Undoing: {op.description}")
                    if op.undo_func():
                        click.echo("Undo successful.")
                    else:
                        click.echo("Undo failed.")
                else:
                    click.echo("Nothing to undo.")
            elif cmd == 'search':
                if len(command_parts) < 2:
                    click.echo("Usage: search <query>")
                    continue
                    
                query = " ".join(command_parts[1:])
                # Get all tasks first and apply advanced search filter locally
                all_tasks = task_manager.list_tasks()
                from gtasks_cli.commands.interactive_utils.search import apply_search_filter
                search_results = apply_search_filter(all_tasks, query)
                if search_results:
                    click.echo(f"\nSearch results for '{query}':")
                    display_tasks_grouped_by_list(search_results)
                    task_state.set_tasks(search_results)
                    task_state.push_command(command_input)
                else:
                    click.echo(f"No tasks found matching '{query}'.")
                    # Keep current tasks unchanged
            elif cmd == 'tags':
                # Handle tag filtering
                from gtasks_cli.commands.interactive_utils.tag_commands import handle_tag_filtering_interactive_mode
                handle_tag_filtering_interactive_mode(task_manager, use_google_tasks)
                # After tag filtering mode, we need to refresh the task display
                _display_tasks_grouped_by_list(task_state.tasks)
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
                    elif subcommand == 'tags':
                        console.print(Panel("[bold blue]Tags Command Help[/bold blue]", expand=False))
                        
                        console.print("[bold]Description:[/bold]")
                        console.print("Filter tasks by tags extracted from task titles, descriptions, and notes.")
                        console.print("Tags are identified as text within square brackets [tag].\n")
                        
                        console.print("[bold]Usage:[/bold]")
                        console.print("  tags\n")
                        
                        console.print("[bold]Examples:[/bold]")
                        console.print("  [green]# Enter tag selection mode[/green]")
                        console.print("  tags\n")
                        console.print("  Then select tags by number to filter tasks.\n")
                        
                        console.print("[bold]Interactive Mode:[/bold]")
                        console.print("In tag selection mode, you can:")
                        console.print("  - View all available tags in a numbered list")
                        console.print("  - Select multiple tags by entering their numbers (e.g., 1,3,5)")
                        console.print("  - Enter 'all' to select all tags")
                        console.print("  - Operate on the filtered tasks with standard commands")
                        console.print("  - Search within the current filtered tasks with the 'search' command")
                        console.print("  - Search within the current filtered tasks with the 'search' command\n")
                    elif subcommand == 'view':
                        show_view_help()
                    elif subcommand == 'done':
                        show_done_help()
                    elif subcommand == 'delete':
                        show_delete_help()
                    elif subcommand == 'update':
                        show_update_help()
                    elif subcommand == 'update-status':
                        from gtasks_cli.commands.interactive_help import show_bulk_update_help
                        show_bulk_update_help()
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


def _view_task_details(task: Task):
    """View detailed information about a task"""
    # Use the imported function for consistency
    view_task_details(task)



