#!/usr/bin/env python3
"""
Add command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Priority

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.option('--title', '-t', required=True, help='Task title')
@click.option('--description', '-d', help='Task description')
@click.option('--due', help='Due date (ISO format, e.g., 2024-12-31 or 2024-12-31T15:30:00)')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              default='medium', help='Task priority')
@click.option('--project', '-p', help='Project name')
@click.option('--tags', '-g', help='Task tags (comma-separated)')
@click.option('--notes', '-n', help='Task notes')
@click.option('--depends-on', '-D', help='Task IDs this task depends on (comma-separated)')
@click.option('--recurring', '-r', help='Recurrence rule (e.g., daily, weekly, monthly, yearly, or "every 2 weeks")')
@click.pass_context
def add(ctx, title, description, due, priority, project, tags, notes, depends_on, recurring):
    """Add a new task
    
    \b
    Examples:
      # Add a simple task
      gtasks add -t "Buy groceries"
      
      # Add a task with due date and priority
      gtasks add -t "Finish report" --due "2024-12-31T17:00:00" --priority high
      
      # Add a task with project and tags
      gtasks add -t "Code review" -p "Project X" --tags "development,review"
      
      # Add a recurring task
      gtasks add -t "Daily standup" --recurring daily
      
      # Add a task with dependencies
      gtasks add -t "Deploy to production" --depends-on "task123,task456"
      
      # Add a task using Google Tasks directly
      gtasks add -t "Team meeting" -g
    """
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Adding task: {title} {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    # Convert priority string to enum
    priority_enum = Priority(priority)
    
    # Parse tags if provided
    tags_list = []
    if tags:
        tags_list = [tag.strip() for tag in tags.split(',')]
    
    # Parse dependencies if provided
    dependencies_list = []
    if depends_on:
        dependencies_list = [dep.strip() for dep in depends_on.split(',')]
    
    # Create task manager and task
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    task = task_manager.create_task(
        title=title,
        description=description,
        due=due,
        priority=priority_enum,
        project=project,
        tags=tags_list,
        notes=notes,
        dependencies=dependencies_list,
        recurrence_rule=recurring
    )
    
    click.echo(f"✅ Task '{title}' (ID: {task.id}) with priority '{priority}' added successfully!")