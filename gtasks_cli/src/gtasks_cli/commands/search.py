#!/usr/bin/env python3
"""
Search command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Priority

# Set up logger
logger = setup_logger(__name__)



@click.command()
@click.argument('query')
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'waiting', 'deleted']), 
              help='Filter by status')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              help='Filter by priority')
@click.option('--project', help='Filter by project')
@click.option('--recurring', '-r', is_flag=True, help='Show only recurring tasks')
@click.pass_context
def search(ctx, query, status, priority, project, recurring):
    """Search for tasks by query string
    
    \b
    Examples:
      # Search for tasks containing "meeting"
      gtasks search meeting
      
      # Search for high priority tasks containing "report"
      gtasks search report --priority high
      
      # Search for completed tasks
      gtasks search done --status completed
      
      # Search using Google Tasks directly
      gtasks search -g "important"
    """
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    storage_backend = ctx.obj.get('storage_backend', 'json')
    logger.info(f"Searching tasks {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    from gtasks_cli.models.task import TaskStatus
    from gtasks_cli.commands.list import task_state
    
    # Create task manager with the selected storage backend
    task_manager = TaskManager(use_google_tasks=use_google_tasks, storage_backend=storage_backend)
    
    # Convert string parameters to enums where needed
    status_enum = TaskStatus(status) if status else None
    priority_enum = Priority(priority) if priority else None
    
    # Search tasks using list_tasks with search parameter
    tasks = task_manager.list_tasks(search=query)
    
    # Apply additional filters
    if status_enum:
        tasks = [t for t in tasks if t.status == status_enum]
        
    if priority_enum:
        tasks = [t for t in tasks if t.priority == priority_enum]
        
    if project:
        tasks = [t for t in tasks if t.project == project]
        
    if recurring:
        tasks = [t for t in tasks if t.is_recurring]
    
    if not tasks:
        click.echo(f"No tasks found matching '{query}'.")
        return
    
    # Store tasks for interactive mode
    task_state.set_tasks(tasks)
    
    click.echo(f"🔍 Found {len(tasks)} task(s) matching '{query}':")
    # Import the display function from list command
    from gtasks_cli.commands.list import _display_tasks
    _display_tasks(tasks)