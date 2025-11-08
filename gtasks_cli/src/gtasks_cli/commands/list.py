#!/usr/bin/env python3
"""
List command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Priority

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'waiting', 'deleted']), 
              help='Filter by status')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              help='Filter by priority')
@click.option('--project', help='Filter by project')
@click.option('--recurring', '-r', is_flag=True, help='Show only recurring tasks')
@click.pass_context
def list(ctx, status, priority, project, recurring):
    """List all tasks
    
    \b
    Examples:
      # List all tasks
      gtasks list
      
      # List only pending tasks
      gtasks list --status pending
      
      # List high priority tasks
      gtasks list --priority high
      
      # List tasks for a specific project
      gtasks list --project "Project X"
      
      # List only recurring tasks
      gtasks list --recurring
      
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
    
    tasks = task_manager.list_tasks(
        status=status_enum,
        priority=priority_enum,
        project=project
    )
    
    # Filter for recurring tasks if requested
    if recurring:
        tasks = [task for task in tasks if task.is_recurring]
    
    if not tasks:
        click.echo("No tasks found.")
        return
    
    click.echo(f"📋 Found {len(tasks)} task(s):")
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
        
        # Format recurrence if present
        recurrence_info = ""
        if task.is_recurring:
            recurrence_info = " 🔁"
        
        click.echo(f"  {status_icon} {priority_icon} {task.title} (ID: {task.id}){due_info}{project_info}{recurrence_info}")