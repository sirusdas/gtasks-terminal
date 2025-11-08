#!/usr/bin/env python3
"""
Done command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.argument('task_id')
@click.pass_context
def done(ctx, task_id):
    """Mark task as done"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Marking task {task_id} as done {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    if task_manager.complete_task(task_id):
        click.echo(f"✅ Task {task_id} marked as done!")
    else:
        # Check if task is blocked by dependencies
        tasks = task_manager.list_tasks()
        task_dict = {t.id: t for t in tasks}
        task = task_dict.get(task_id)
        if task and not task_manager._can_complete_task(task, tasks):
            click.echo(f"❌ Task {task_id} cannot be completed because it has unmet dependencies!")
        else:
            click.echo(f"❌ Task {task_id} not found!")
        exit(1)