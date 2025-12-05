#!/usr/bin/env python3
"""
Tag selection commands for interactive mode
"""

import click
from typing import List, Set
from collections import defaultdict

from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task
from gtasks_cli.utils.tag_extractor import extract_tags_from_task
from gtasks_cli.commands.interactive_utils.display import display_tasks_grouped_by_list
from gtasks_cli.commands.interactive_utils.task_details import view_task_details
import os

# Try to import prompt_toolkit for enhanced command line experience
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import FileHistory, InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

logger = setup_logger(__name__)


def handle_tags_command(task_manager, use_google_tasks: bool = False):
    """Handle the tags command in interactive mode - display tags and allow selection"""
    try:
        # Load all tasks
        tasks = task_manager.list_tasks()
        logger.info(f"Loaded {len(tasks)} tasks for tag listing")
        
        if not tasks:
            click.echo("No tasks found.")
            return []  # Return empty list
        
        # Extract all tags
        all_tags = set()
        tag_to_tasks = defaultdict(list)
        
        for task in tasks:
            task_tags = extract_tags_from_task(task)
            for tag in task_tags:
                all_tags.add(tag)
                tag_to_tasks[tag].append(task)
        
        if not all_tags:
            click.echo("No tags found in any tasks.")
            return []  # Return empty list
        
        # Sort tags
        sorted_tags = sorted(list(all_tags))
        
        # Display tags in columns with numbers
        click.echo("\nAvailable Tags:")
        click.echo("=" * 50)
        
        # Calculate number of columns (aim for 4 columns)
        tags_count = len(sorted_tags)
        num_columns = 4
        tags_per_column = (tags_count + num_columns - 1) // num_columns  # Ceiling division
        
        # Group tags into columns
        columns = []
        for i in range(num_columns):
            start_idx = i * tags_per_column
            end_idx = min(start_idx + tags_per_column, tags_count)
            column = sorted_tags[start_idx:end_idx]
            columns.append(column)
        
        # Display tags in columns with proper alignment
        for row_idx in range(tags_per_column):
            row_display = ""
            for col_idx in range(num_columns):
                if row_idx < len(columns[col_idx]):
                    tag_index = col_idx * tags_per_column + row_idx + 1
                    tag = columns[col_idx][row_idx]
                    row_display += f"{tag_index:2d}. {tag:<20} "
                else:
                    # Empty cell
                    row_display += " " * 24
            click.echo(row_display.rstrip())
        
        click.echo(f"\nTotal: {len(sorted_tags)} tags")
        click.echo("\nEnter tag numbers separated by commas (e.g., 1,3,5), tag names separated by | (e.g., my|prasen), or 'all' for all tags.")
        click.echo("Press Enter to cancel.")
        
        # Get user input
        user_input = click.prompt("Select tags", type=str, default="", show_default=False).strip()
        
        if not user_input:
            click.echo("Tag selection cancelled.")
            return []  # Return empty list
        
        # Check if user entered tag names directly (with OR logic using |)
        if '|' in user_input or not user_input.isdigit():
            # Handle direct tag name input
            # Split on pipe for OR logic
            tag_names = [name.strip() for name in user_input.split('|')]
            
            # Find matching tags (partial match is fine)
            selected_tags = []
            for tag_name in tag_names:
                # Look for exact or partial matches
                matches = [tag for tag in sorted_tags if tag_name.lower() in tag.lower()]
                selected_tags.extend(matches)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_selected_tags = []
            for tag in selected_tags:
                if tag not in seen:
                    seen.add(tag)
                    unique_selected_tags.append(tag)
            
            selected_tags = unique_selected_tags
            
            if not selected_tags:
                click.echo(f"No tags found matching: {user_input}")
                return []  # Return empty list
        elif user_input.lower() == 'all':
            selected_tags = sorted_tags
        else:
            # Parse selected tag numbers
            try:
                selected_indices = [int(x.strip()) for x in user_input.split(',') if x.strip()]
                # Validate indices
                invalid_indices = [i for i in selected_indices if i < 1 or i > len(sorted_tags)]
                if invalid_indices:
                    click.echo(f"Invalid tag numbers: {invalid_indices}. Please enter valid numbers.")
                    return []  # Return empty list
                
                # Get selected tags
                selected_tags = [sorted_tags[i - 1] for i in selected_indices]
            except ValueError:
                click.echo("Invalid input. Please enter comma-separated numbers, tag names separated by |, or 'all'.")
                return []  # Return empty list
        
        # Get tasks matching selected tags
        selected_tasks = []
        seen_task_ids = set()
        
        for tag in selected_tags:
            for task in tag_to_tasks[tag]:
                if task.id not in seen_task_ids:
                    selected_tasks.append(task)
                    seen_task_ids.add(task.id)
        
        if not selected_tasks:
            click.echo("No tasks found with the selected tags.")
            return []  # Return empty list
        
        # Display tasks and get the displayed order
        click.echo(f"\nFound {len(selected_tasks)} tasks with selected tags: {', '.join(selected_tags)}")
        displayed_tasks = display_tasks_grouped_by_list(selected_tasks)
        
        return displayed_tasks
        
    except Exception as e:
        logger.error(f"Error in handle_tags_command: {e}")
        click.echo(f"An error occurred while processing tags: {e}")
        return []  # Return empty list


def handle_tag_filtering_interactive_mode(task_manager, use_google_tasks: bool = False):
    """Enter interactive mode for tag-based task filtering"""
    try:
        # Show tags and get selected tasks
        tasks = handle_tags_command(task_manager, use_google_tasks)
        
        if not tasks:
            return
        
        # Enter a simplified interactive mode for the selected tasks
        _enter_tag_filtered_interactive_mode(tasks, task_manager, use_google_tasks)
        
    except Exception as e:
        logger.error(f"Error in handle_tag_filtering_interactive_mode: {e}")
        click.echo(f"An error occurred: {e}")


def _search_tasks_in_list(tasks: List[Task], query: str) -> List[Task]:
    """Search for tasks within a list based on a query string"""
    if not query:
        return tasks
        
    query = query.lower().strip()
    if not query:
        return tasks
    
    # Split query on pipe for OR logic
    search_terms = [term.strip() for term in query.split('|')] if '|' in query else [query]
    
    matching_tasks = []
    for task in tasks:
        # Check if any search term matches title, description, or notes
        task_matches = False
        for term in search_terms:
            if (term in (task.title or '').lower() or 
                term in (task.description or '').lower() or 
                term in (task.notes or '').lower()):
                task_matches = True
                break
        
        if task_matches:
            matching_tasks.append(task)
    
    return matching_tasks


def _enter_tag_filtered_interactive_mode(tasks: List[Task], task_manager, use_google_tasks: bool):
    """Enter a simplified interactive mode for tag-filtered tasks"""
    try:
        # Import required modules
        from gtasks_cli.commands.interactive_utils.done_commands import handle_done_command
        from gtasks_cli.commands.interactive_utils.delete_commands import handle_delete_command
        from gtasks_cli.commands.interactive_utils.update_commands import handle_update_command
        from gtasks_cli.commands.interactive_utils.add_commands import handle_add_command
        from gtasks_cli.commands.interactive_utils.bulk_update_commands import handle_bulk_update_command
        from gtasks_cli.commands.interactive_utils.update_tags_commands import handle_update_tags_command
        
        # Keep a reference to the original tasks for search operations
        original_tasks = tasks
        
        # Command history for prompt_toolkit
        if HAS_PROMPT_TOOLKIT:
            history_file = os.path.expanduser("~/.gtasks_history")
            try:
                history = FileHistory(history_file)
            except Exception as e:
                logger.warning(f"Could not create history file at {history_file}: {e}. Using in-memory history.")
                history = InMemoryHistory()

        # Command loop
        while True:
            click.echo("\nEnter command (view <num>, done <num>, delete <num>, update <num>, add, update-status <spec>, update-tags <spec>, search <query>, back, quit):")
            
            # Use prompt_toolkit for better command line experience if available
            if HAS_PROMPT_TOOLKIT:
                user_input = prompt(
                    "Command: ",
                    history=history if HAS_PROMPT_TOOLKIT else None,
                    auto_suggest=AutoSuggestFromHistory() if HAS_PROMPT_TOOLKIT else None
                ).strip()
            else:
                user_input = click.prompt("Command", type=str, default="", show_default=False).strip()
            
            if not user_input:
                continue
            
            parts = user_input.split()
            cmd = parts[0].lower()
            
            if cmd in ['quit', 'exit']:
                click.echo("Exiting tag-filtered interactive mode.")
                break
            elif cmd == 'back':
                click.echo("Returning to tag selection.")
                # Re-run tag selection
                tasks = handle_tags_command(task_manager, use_google_tasks)
                original_tasks = tasks  # Reset original tasks to the new selection
                if not tasks:
                    break
                continue
            elif cmd == 'view':
                if len(parts) < 2:
                    click.echo("Usage: view <number>")
                    continue
                
                try:
                    task_num = int(parts[1])
                    if task_num < 1 or task_num > len(tasks):
                        click.echo(f"Invalid task number. Please enter a number between 1 and {len(tasks)}.")
                        continue
                    
                    # Get the task by its position in the current tasks list
                    task = tasks[task_num - 1]
                    view_task_details(task)
                except ValueError:
                    click.echo("Invalid task number. Please enter a valid integer.")
            elif cmd == 'search':
                if len(parts) < 2:
                    click.echo("Usage: search <query>")
                    continue
                
                # Join all parts after 'search' to handle complex queries correctly
                query = " ".join(parts[1:])
                # Remove surrounding quotes if present (but preserve internal structure)
                if (query.startswith('"') and query.endswith('"') and len(query) > 1) or \
                   (query.startswith("'") and query.endswith("'") and len(query) > 1):
                    query = query[1:-1]
                
                # Search within the original tasks (before any previous search filtering)
                search_results = _search_tasks_in_list(original_tasks, query)
                
                if search_results:
                    click.echo(f"\nFound {len(search_results)} tasks matching '{query}':")
                    tasks = display_tasks_grouped_by_list(search_results)
                    # Update original_tasks to the new search results so subsequent searches 
                    # work on the current filtered set
                    original_tasks = search_results
                else:
                    click.echo(f"No tasks found matching '{query}'.")
                    # Keep current tasks unchanged
            elif cmd == 'add':
                handle_add_command(None, task_manager, ['add'], use_google_tasks)
                # Refresh task list after adding
                tasks = handle_tags_command(task_manager, use_google_tasks)
                original_tasks = tasks  # Reset original tasks to the new selection
                if not tasks:
                    break
            elif cmd == 'done':
                # Create a temporary task_state-like object
                class TempTaskState:
                    def __init__(self, tasks_list):
                        self.tasks = tasks_list
                    
                    def get_task_by_number(self, number):
                        if 1 <= number <= len(self.tasks):
                            return self.tasks[number - 1]
                        return None
                
                temp_state = TempTaskState(tasks)
                handle_done_command(temp_state, task_manager, ['done'] + parts[1:], use_google_tasks)
                # Refresh task list after marking as done
                tasks = handle_tags_command(task_manager, use_google_tasks)
                original_tasks = tasks  # Reset original tasks to the new selection
                if not tasks:
                    break
            elif cmd == 'delete':
                # Create a temporary task_state-like object
                class TempTaskState:
                    def __init__(self, tasks_list):
                        self.tasks = tasks_list
                    
                    def get_task_by_number(self, number):
                        if 1 <= number <= len(self.tasks):
                            return self.tasks[number - 1]
                        return None
                
                temp_state = TempTaskState(tasks)
                handle_delete_command(temp_state, task_manager, ['delete'] + parts[1:], use_google_tasks)
                # Refresh task list after deleting
                tasks = handle_tags_command(task_manager, use_google_tasks)
                original_tasks = tasks  # Reset original tasks to the new selection
                if not tasks:
                    break
            elif cmd == 'update':
                # Create a temporary task_state-like object
                class TempTaskState:
                    def __init__(self, tasks_list):
                        self.tasks = tasks_list
                    
                    def get_task_by_number(self, number):
                        if 1 <= number <= len(self.tasks):
                            return self.tasks[number - 1]
                        return None
                
                temp_state = TempTaskState(tasks)
                handle_update_command(temp_state, task_manager, ['update'] + parts[1:], use_google_tasks)
                # Refresh task list after updating
                tasks = handle_tags_command(task_manager, use_google_tasks)
                original_tasks = tasks  # Reset original tasks to the new selection
                if not tasks:
                    break
            elif cmd == 'update-status':
                # Create a temporary task_state-like object
                class TempTaskState:
                    def __init__(self, tasks_list):
                        self.tasks = tasks_list
                
                temp_state = TempTaskState(tasks)
                handle_bulk_update_command(temp_state, task_manager, ['update-status'] + parts[1:], use_google_tasks)
                # Refresh task list after bulk updating
                tasks = handle_tags_command(task_manager, use_google_tasks)
                original_tasks = tasks  # Reset original tasks to the new selection
                if not tasks:
                    break
            elif cmd == 'update-tags':
                # Create a temporary task_state-like object
                class TempTaskState:
                    def __init__(self, tasks_list):
                        self.tasks = tasks_list
                    
                    def get_task_by_number(self, number):
                        if 1 <= number <= len(self.tasks):
                            return self.tasks[number - 1]
                        return None
                
                temp_state = TempTaskState(tasks)
                handle_update_tags_command(temp_state, task_manager, ['update-tags'] + parts[1:], use_google_tasks)
                # Refresh task list after updating tags
                tasks = handle_tags_command(task_manager, use_google_tasks)
                original_tasks = tasks  # Reset original tasks to the new selection
                if not tasks:
                    break
            else:
                click.echo(f"Unknown command: {cmd}. Available commands: view, done, delete, update, add, update-status, update-tags, search, back, quit")
                
    except Exception as e:
        logger.error(f"Error in _enter_tag_filtered_interactive_mode: {e}")
        click.echo(f"An error occurred in interactive mode: {e}")