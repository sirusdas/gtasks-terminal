#!/usr/bin/env python3
"""
Delete command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.argument('task_id')
@click.pass_context
def delete(ctx, task_id):
    """Delete a task"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Deleting task {task_id} {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    # Try to delete the task (mark as deleted)
    if task_manager.delete_task(task_id):
        click.echo(f"🗑️ Task {task_id} deleted!")
    else:
        click.echo(f"❌ Task {task_id} not found!")
        exit(1)