#!/usr/bin/env python3
"""
List selection commands for interactive mode
"""

import click
import os
from typing import List, Dict, Any
from collections import defaultdict

from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.commands.interactive_utils.display import display_tasks_grouped_by_list
from gtasks_cli.commands.interactive_utils.task_details import view_task_details
from gtasks_cli.commands.interactive_utils.add_commands import handle_add_command
from gtasks_cli.commands.interactive_utils.done_commands import handle_done_command
from gtasks_cli.commands.interactive_utils.delete_commands import handle_delete_command
from gtasks_cli.commands.interactive_utils.update_commands import handle_update_command
from gtasks_cli.commands.interactive_utils.bulk_update_commands import handle_bulk_update_command

logger = setup_logger(__name__)


def handle_list_selection_command(task_manager, use_google_tasks: bool = False):
    """
    Handle the list selection command in interactive mode - display task lists and allow selection
    
    Returns:
        List[Task]: Tasks from the selected list
    """
    try:
        if use_google_tasks:
            # For Google Tasks, we need to get the actual task lists from Google
            from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
            client = GoogleTasksClient(account_name=task_manager.account_name)
            
            # Make sure we're connected
            if not client.connect():
                click.echo("Failed to connect to Google Tasks API.")
                return []
            
            # Get task lists
            tasklists = client.list_tasklists()
        else:
            # For local mode, we need to get lists from tasks themselves
            tasks = task_manager.list_tasks()
            list_names = set()
            for task in tasks:
                list_title = getattr(task, 'list_title', 'Tasks')
                list_names.add(list_title)
            
            # Create pseudo tasklists for local mode
            tasklists = [{'id': name, 'title': name} for name in sorted(list_names)]
        
        if not tasklists:
            click.echo("No task lists found.")
            return []
        
        # Sort tasklists by title
        sorted_tasklists = sorted(tasklists, key=lambda x: x.get('title', ''))
        
        # Display lists in columns with numbers
        click.echo("\nAvailable Task Lists:")
        click.echo("=" * 50)
        
        # Calculate number of columns (aim for 4 columns)
        lists_count = len(sorted_tasklists)
        num_columns = 4
        lists_per_column = (lists_count + num_columns - 1) // num_columns  # Ceiling division
        
        # Group lists into columns
        columns = []
        for i in range(num_columns):
            start_idx = i * lists_per_column
            end_idx = min(start_idx + lists_per_column, lists_count)
            column = sorted_tasklists[start_idx:end_idx]
            columns.append(column)
        
        # Display lists in columns with proper alignment
        for row_idx in range(lists_per_column):
            row_display = ""
            for col_idx in range(num_columns):
                if row_idx < len(columns[col_idx]):
                    list_index = col_idx * lists_per_column + row_idx + 1
                    tasklist = columns[col_idx][row_idx]
                    title = tasklist.get('title', 'Untitled')
                    row_display += f"{list_index:2d}. {title:<20} "
                else:
                    # Empty cell
                    row_display += " " * 24
            click.echo(row_display.rstrip())
        
        click.echo(f"\nTotal: {len(sorted_tasklists)} lists")
        click.echo("\nEnter list number to select, or press Enter to cancel.")
        
        # Get user input
        user_input = click.prompt("Select list", type=str, default="", show_default=False).strip()
        
        if not user_input:
            click.echo("List selection cancelled.")
            return []
        
        # Parse selected list number
        try:
            selected_index = int(user_input)
            # Validate index
            if selected_index < 1 or selected_index > len(sorted_tasklists):
                click.echo(f"Invalid list number: {selected_index}. Please enter a valid number.")
                return []
            
            # Get selected list
            selected_list = sorted_tasklists[selected_index - 1]
            selected_list_id = selected_list['id']
            selected_list_title = selected_list.get('title', 'Untitled')
            
        except ValueError:
            click.echo("Invalid input. Please enter a valid list number.")
            return []
        
        # Get tasks for the selected list
        if use_google_tasks:
            # For Google Tasks, get tasks filtered by tasklist_id
            all_tasks = task_manager.list_tasks()
            selected_tasks = [t for t in all_tasks if getattr(t, 'tasklist_id', None) == selected_list_id]
        else:
            # For local mode, get tasks with matching list_title
            all_tasks = task_manager.list_tasks()
            selected_tasks = [t for t in all_tasks if getattr(t, 'list_title', 'Tasks') == selected_list_title]
        
        # Filter for pending tasks only
        pending_tasks = [t for t in selected_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
        
        if not pending_tasks:
            click.echo(f"No pending tasks found in '{selected_list_title}'.")
            return []
        
        # Display tasks and get the displayed order
        click.echo(f"\nFound {len(pending_tasks)} pending tasks in '{selected_list_title}':")
        displayed_tasks = display_tasks_grouped_by_list(pending_tasks)
        
        return displayed_tasks
        
    except Exception as e:
        logger.error(f"Error in handle_list_selection_command: {e}")
        click.echo(f"An error occurred while processing list selection: {e}")
        return []


def handle_list_filtering_interactive_mode(task_manager, use_google_tasks: bool = False):
    """Enter interactive mode for list-based task filtering"""
    try:
        # Show lists and get selected tasks
        tasks = handle_list_selection_command(task_manager, use_google_tasks)
        
        if not tasks:
            return
        
        # Enter a simplified interactive mode for the selected tasks
        _enter_list_filtered_interactive_mode(tasks, task_manager, use_google_tasks)
        
    except Exception as e:
        logger.error(f"Error in handle_list_filtering_interactive_mode: {e}")
        click.echo(f"An error occurred: {e}")


def _enter_list_filtered_interactive_mode(tasks: List[Task], task_manager, use_google_tasks: bool):
    """Internal function to enter interactive mode with pre-filtered tasks"""
    from gtasks_cli.commands.interactive_utils.common import (
        refresh_task_list
    )
    
    # Try to import prompt_toolkit for enhanced command line experience
    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.history import FileHistory, InMemoryHistory
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        HAS_PROMPT_TOOLKIT = True
    except ImportError:
        HAS_PROMPT_TOOLKIT = False
    
    import shlex
    
    # Store tasks in a simple state object
    class SimpleTaskState:
        def __init__(self, tasks):
            self.tasks = tasks
            self.default_tasks = tasks[:]
        
        def get_task_by_number(self, num):
            if 1 <= num <= len(self.tasks):
                return self.tasks[num - 1]
            return None
        
        def set_tasks(self, tasks):
            self.tasks = tasks
    
    task_state = SimpleTaskState(tasks)
    
    # Command history for prompt_toolkit
    if HAS_PROMPT_TOOLKIT:
        history_file = os.path.expanduser("~/.gtasks_history")
        try:
            history = FileHistory(history_file)
        except Exception as e:
            logger.warning(f"Could not create history file at {history_file}: {e}. Using in-memory history.")
            history = InMemoryHistory()
    
    click.echo("\n" + "="*50)
    click.echo("Entering list-filtered interactive mode")
    click.echo("Commands: view, done, delete, update, update-status, add, search, back, quit/exit")
    click.echo("Type 'help' for detailed command information")
    click.echo("="*50)
    
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
            elif cmd == 'back':
                # Go back to list selection
                click.echo("Returning to list selection...")
                handle_list_filtering_interactive_mode(task_manager, use_google_tasks)
                break
            elif cmd == 'view':
                if len(command_parts) < 2:
                    click.echo("Usage: view <number>")
                    continue
                    
                try:
                    task_num = int(command_parts[1])
                    task = task_state.get_task_by_number(task_num)
                    if task:
                        view_task_details(task)
                    else:
                        click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.tasks)}.")
                except ValueError:
                    click.echo("Invalid task number. Please enter a valid integer.")
            elif cmd == 'add':
                # Import and use the add command handler
                from gtasks_cli.commands.interactive_utils.add_commands import handle_add_command
                handle_add_command(task_state, task_manager, command_parts, use_google_tasks)
                # Refresh task list after adding
                refresh_task_list(task_manager, task_state, use_google_tasks)
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
            elif cmd == 'search':
                if len(command_parts) < 2:
                    click.echo("Usage: search <query>")
                    continue
                    
                query = " ".join(command_parts[1:]).lower()
                matching_tasks = []
                for task in task_state.tasks:
                    if (query in task.title.lower() or 
                        (task.description and query in task.description.lower()) or
                        (task.notes and query in task.notes.lower())):
                        matching_tasks.append(task)
                
                if matching_tasks:
                    click.echo(f"\nSearch results for '{query}':")
                    display_tasks_grouped_by_list(matching_tasks)
                    task_state.set_tasks(matching_tasks)
                else:
                    click.echo(f"No tasks found matching '{query}'.")
            elif cmd == 'help':
                _show_list_filtered_help()
            else:
                click.echo(f"Unknown command: {cmd}. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            click.echo("\nUse 'quit' or 'exit' to exit interactive mode.")
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}", exc_info=True)
            click.echo(f"An error occurred: {e}")


def _show_list_filtered_help():
    """Show help for the list-filtered interactive mode"""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    
    console = Console()
    
    console.print(Panel("[bold blue]List-Filtered Interactive Mode Help[/bold blue]", expand=False))
    
    console.print("[bold]Available Commands:[/bold]")
    console.print("  [green]view <number>[/green]           - View detailed information about a task")
    console.print("  [green]done <number>[/green]           - Mark a task as completed")
    console.print("  [green]delete <number>[/green]         - Delete a task")
    console.print("  [green]update <number>[/green]         - Update task properties")
    console.print("  [green]update-status <spec>[/green]    - Bulk update task status and due dates")
    console.print("  [green]add[/green]                     - Add a new task to the current list")
    console.print("  [green]search <query>[/green]          - Search for tasks within the current list")
    console.print("  [green]back[/green]                    - Return to list selection")
    console.print("  [green]quit[/green] or [green]exit[/green]          - Exit interactive mode")
    console.print("  [green]help[/green]                    - Show this help message\n")
    
    console.print("[bold]Examples:[/bold]")
    console.print("  view 1")
    console.print("  done 3")
    console.print("  update 2")
    console.print("  update-status C1,P3")
    console.print("  search meeting")
    console.print("  add")