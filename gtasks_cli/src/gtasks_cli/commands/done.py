#!/usr/bin/env python3
"""
Mark task as done command for the Google Tasks CLI application.
"""

import click
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


@click.command()
@click.argument('task_identifier')
@click.pass_context
def done(ctx, task_identifier):
    """Mark a task as completed."""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'json')
    
    # Create task manager with the selected storage backend
    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend
    )
    
    # First try to complete by ID directly
    success = task_manager.complete_task(task_identifier)
    
    # If that fails, try to find the task by title
    if not success:
        tasks = task_manager.list_tasks()
        for task in tasks:
            # Check if the identifier matches the task title
            if task.title and task_identifier.lower() in task.title.lower():
                success = task_manager.complete_task(task.id)
                if success:
                    task_identifier = task.title  # Update for the success message
                    break
    
    if success:
        click.echo(f"Task marked as completed: {task_identifier}")
        logger.info(f"Task marked as completed: {task_identifier}")
    else:
        click.echo(f"Failed to mark task as completed: {task_identifier}")
        logger.error(f"Failed to mark task as completed: {task_identifier}")