#!/usr/bin/env python3
"""
Piped command handler for interactive mode.
Supports chaining commands like: search "my" --cur --id 89 | view
"""

import shlex
import click
from typing import List, Tuple, Optional
from gtasks_cli.models.task import Task
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


def parse_piped_command(command_input: str) -> List[List[str]]:
    """
    Parse a piped command into stages.
    
    Args:
        command_input: Raw command input string
        
    Returns:
        List of command parts for each stage
        
    Example:
        "search 'my' --cur --id 89 | view" -> 
        [['search', 'my', '--cur', '--id', '89'], ['view']]
    """
    # Split by pipe character
    stages = command_input.split('|')
    
    parsed_stages = []
    for stage in stages:
        stage = stage.strip()
        if stage:
            try:
                # Use shlex to properly handle quotes
                parts = shlex.split(stage)
                parsed_stages.append(parts)
            except ValueError as e:
                logger.error(f"Error parsing command stage '{stage}': {e}")
                raise
    
    return parsed_stages


def execute_search_stage(command_parts: List[str], task_state, task_manager, use_google_tasks: bool) -> List[Task]:
    """
    Execute a search command stage with support for --cur, --id, --ids flags.
    
    Args:
        command_parts: Command parts (e.g., ['search', 'my', '--cur', '--id', '89'])
        task_state: Current task state
        task_manager: Task manager instance
        use_google_tasks: Whether using Google Tasks
        
    Returns:
        List of tasks matching the search
    """
    if len(command_parts) < 2:
        click.echo("Usage: search <query> [--cur] [--id <num>] [--ids <num1,num2,...>]")
        return []
    
    # Parse flags
    use_current = '--cur' in command_parts
    task_id = None
    task_ids = []
    query_parts = []
    
    i = 1  # Skip 'search'
    while i < len(command_parts):
        part = command_parts[i]
        
        if part == '--cur':
            use_current = True
            i += 1
        elif part == '--id' and i + 1 < len(command_parts):
            try:
                task_id = int(command_parts[i + 1])
                i += 2
            except ValueError:
                click.echo(f"Invalid task number: {command_parts[i + 1]}")
                return []
        elif part == '--ids' and i + 1 < len(command_parts):
            try:
                task_ids = [int(x.strip()) for x in command_parts[i + 1].split(',')]
                i += 2
            except ValueError:
                click.echo(f"Invalid task numbers: {command_parts[i + 1]}")
                return []
        else:
            query_parts.append(part)
            i += 1
    
    # Build query
    query = " ".join(query_parts)
    
    # Determine which tasks to search in
    if task_id is not None:
        # Search in specific task
        task = task_state.get_task_by_number(task_id)
        if not task:
            click.echo(f"Invalid task number: {task_id}")
            return []
        search_pool = [task]
    elif task_ids:
        # Search in specific tasks
        search_pool = []
        for tid in task_ids:
            task = task_state.get_task_by_number(tid)
            if task:
                search_pool.append(task)
            else:
                click.echo(f"Warning: Invalid task number {tid}, skipping")
    elif use_current:
        # Search in current tasks
        search_pool = task_state.tasks
    else:
        # Default: search in current tasks
        search_pool = task_state.tasks
    
    # Apply search filter
    from gtasks_cli.commands.interactive_utils.search import apply_search_filter
    search_results = apply_search_filter(search_pool, query)
    
    return search_results


def execute_view_stage(tasks: List[Task], task_state) -> None:
    """
    Execute a view command stage on the given tasks.
    
    Args:
        tasks: Tasks to view
        task_state: Current task state
    """
    from gtasks_cli.commands.interactive_utils.task_details import view_task_details
    
    if not tasks:
        click.echo("No tasks to view.")
        return
    
    if len(tasks) == 1:
        # Single task, view it directly
        view_task_details(tasks[0])
    else:
        # Multiple tasks, view each one
        click.echo(f"\nFound {len(tasks)} tasks. Viewing all:\n")
        for i, task in enumerate(tasks, 1):
            click.echo(f"\n{'='*80}")
            click.echo(f"Task {i} of {len(tasks)}")
            click.echo(f"{'='*80}\n")
            view_task_details(task)


def handle_piped_command(command_input: str, task_state, task_manager, use_google_tasks: bool) -> bool:
    """
    Handle a piped command in interactive mode.
    
    Args:
        command_input: Raw command input
        task_state: Current task state
        task_manager: Task manager instance
        use_google_tasks: Whether using Google Tasks
        
    Returns:
        True if command was handled, False otherwise
    """
    try:
        stages = parse_piped_command(command_input)
        
        if len(stages) < 2:
            return False  # Not a piped command
        
        # Execute first stage
        first_cmd = stages[0][0].lower()
        
        if first_cmd != 'search':
            click.echo("Error: Only 'search' command is supported as the first stage in pipes")
            return True
        
        # Execute search
        results = execute_search_stage(stages[0], task_state, task_manager, use_google_tasks)
        
        if not results:
            click.echo("No results found.")
            return True
        
        # Execute subsequent stages
        for stage_parts in stages[1:]:
            if not stage_parts:
                continue
            
            stage_cmd = stage_parts[0].lower()
            
            if stage_cmd == 'view':
                execute_view_stage(results, task_state)
            else:
                click.echo(f"Error: Unsupported piped command '{stage_cmd}'")
                return True
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling piped command: {e}")
        click.echo(f"Error executing piped command: {e}")
        return True
