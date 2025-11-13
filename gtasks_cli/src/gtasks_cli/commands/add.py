#!/usr/bin/env python3
"""
Add command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Priority
from gtasks_cli.core.task_manager import TaskManager

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.option('--title', '-t', required=True, help='Task title')
@click.option('--description', '-d', help='Task description')
@click.option('--due', '-u', help='Due date/time (ISO format)')
@click.option('--priority', '-p', type=click.Choice([p.value for p in Priority]), 
              default=Priority.MEDIUM.value, help='Task priority')
@click.option('--project', '-j', help='Project name')
@click.option('--tags', '-g', multiple=True, help='Task tags')
@click.option('--list-name', '-l', help='Task list name (for local mode)')
@click.option('--notes', '-n', help='Additional notes')
@click.option('--recurring', '-r', help='Recurrence rule (e.g., "RRULE:FREQ=DAILY")')
@click.pass_context
def add(ctx, title, description, due, priority, project, tags, list_name, notes, recurring):
    """Add a new task."""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'json')
    
    # Create task manager with the selected storage backend
    task_manager = TaskManager(use_google_tasks=use_google_tasks, storage_backend=storage_backend)
    
    # Convert priority string back to enum
    priority_enum = Priority(priority)
    
    # Create the task
    task = task_manager.create_task(
        title=title,
        description=description,
        due=due,
        priority=priority_enum,
        project=project,
        tags=list(tags),
        notes=notes,
        recurrence_rule=recurring,
        tasklist_name=list_name
    )
    
    if task:
        click.echo(f"Task created successfully: {task.title} (ID: {task.id})")
        logger.info(f"Created task: {task.title}")
    else:
        click.echo("Failed to create task")
        logger.error("Failed to create task")