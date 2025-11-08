#!/usr/bin/env python3
"""
Search command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.argument('query')
@click.pass_context
def search(ctx, query):
    """Search tasks by query string
    
    \b
    Examples:
      # Search for tasks containing "meeting"
      gtasks search meeting
      
      # Search using Google Tasks directly
      gtasks search "important" -g
    """
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    use_offline = ctx.obj.get('OFFLINE_MODE', False)
    
    if use_offline and use_google_tasks:
        logger.info("Operating in offline mode - searching local tasks only")
        use_google_tasks = False
    
    logger.info(f"Searching tasks with query: {query} {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    # Create task manager
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    # Search tasks
    tasks = task_manager.search_tasks(query)
    
    if not tasks:
        click.echo("No tasks found matching your query.")
        return
    
    click.echo(f"🔍 Found {len(tasks)} task(s) matching '{query}':")
    for task in tasks:
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
            due_info = f" 📅 {task.due}"
        
        # Format project if present
        project_info = ""
        if task.project:
            project_info = f" 📁 {task.project}"
        
        click.echo(f"  {status_icon} {priority_icon} {task.title} (ID: {task.id}){due_info}{project_info}")