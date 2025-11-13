#!/usr/bin/env python3
"""
Search command for Google Tasks CLI
"""

import click
from typing import List
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Task, TaskStatus, Priority

# Set up logger
logger = setup_logger(__name__)



@click.command()
@click.argument('query', required=False)
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'waiting', 'deleted']),
              help='Filter by status')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']),
              help='Filter by priority')
@click.option('--project', help='Filter by project')
@click.option('--recurring', '-r', is_flag=True, help='Show only recurring tasks')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def search(ctx, query, status, priority, project, recurring, account):
    """Search for tasks by keywords.
    
    QUERY: Search terms (can use | for multiple terms)
    """
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'json')
    
    # Determine the account to use
    if account:
        # Explicitly specified account
        account_name = account
    else:
        # Check context object for account
        account_name = ctx.obj.get('account_name')
    
    logger.info(f"Searching tasks {'(Google Tasks)' if use_google_tasks else '(Local)'} for account: {account_name or 'default'}")
    
    # Create task manager with account support
    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend,
        account_name=account_name
    )
    
    # Search tasks
    try:
        tasks = task_manager.list_tasks(search=query)
    except Exception as e:
        logger.error(f"Error searching tasks: {e}")
        click.echo(f"❌ Error searching tasks: {e}")
        return
    
    # Apply additional filters
    from gtasks_cli.models.task import TaskStatus
    status_enum = TaskStatus(status) if status else None
    if status_enum:
        tasks = [t for t in tasks if t.status == status_enum]
        
    from gtasks_cli.models.task import Priority
    priority_enum = Priority(priority) if priority else None
    if priority_enum:
        tasks = [t for t in tasks if t.priority == priority_enum]
        
    if project:
        tasks = [t for t in tasks if t.project == project]
        
    if recurring:
        tasks = [t for t in tasks if t.is_recurring]
    
    if use_google_tasks:
        tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
    
    if not tasks:
        click.echo("No tasks found matching your search criteria.")
        return
    
    # Store tasks for interactive mode
    from gtasks_cli.commands.list import task_state
    task_state.set_tasks(tasks)
    
    click.echo(f"🔍 Found {len(tasks)} task(s):")
    # Display tasks grouped by list names with color coding
    from gtasks_cli.utils.display import display_tasks_grouped_by_list
    display_tasks_grouped_by_list(tasks)