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
@click.argument('title')
@click.option('--description', '-d', help='Task description')
@click.option('--due', '-D', help='Due date (ISO format or natural language)')
@click.option('--priority', '-p', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              default='medium', help='Task priority')
@click.option('--project', '-P', help='Project name')
@click.option('--tags', '-t', multiple=True, help='Task tags')
@click.option('--notes', '-n', help='Additional notes')
@click.option('--recurrence', '-r', help='Recurrence rule (e.g., "daily", "weekly", "monthly")')
@click.option('--list-name', '-l', help='Task list name')
@click.option('--estimated-duration', '-e', type=int, help='Estimated duration in minutes')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def add(ctx, title, description, due, priority, project, tags, notes, recurrence, list_name, estimated_duration, account):
    """Add a new task."""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'json')
    
    # Determine the account to use
    if account:
        # Explicitly specified account
        account_name = account
    else:
        # Check context object for account
        account_name = ctx.obj.get('account_name')
    
    logger.info(f"Adding task {'(Google Tasks)' if use_google_tasks else '(Local)'} for account: {account_name or 'default'}")
    
    # Create task manager with account support
    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend,
        account_name=account_name
    )
    
    # Convert priority string to enum
    priority_enum = Priority[priority.upper()]
    
    # Create the task
    task = task_manager.create_task(
        title=title,
        description=description,
        due=due,
        priority=priority_enum,
        project=project,
        tags=list(tags),
        notes=notes,
        recurrence_rule=recurrence,
        tasklist_name=list_name
    )
    
    if task:
        click.echo(f"✅ Task added successfully: {task.title}")
        logger.info(f"Task added successfully: {task.title}")
        
        # Check for auto-save (CLI option overrides config)
        from gtasks_cli.storage.config_manager import ConfigManager
        config_manager = ConfigManager(account_name=account_name)
        cli_auto_save = ctx.obj.get('auto_save')
        
        # Use CLI option if provided, otherwise use config
        if cli_auto_save is not None:
            auto_save = cli_auto_save
        else:
            auto_save = config_manager.get('sync.auto_save', False)
        
        if not use_google_tasks and auto_save:
            from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager
            
            click.echo("Auto-saving to Google Tasks...")
            sync_manager = AdvancedSyncManager(task_manager.storage, task_manager.google_client)
            if sync_manager.sync_single_task(task, 'create', old_task_id=task.id):
                 click.echo("✅ Auto-saved to Google Tasks")
            else:
                 click.echo("⚠️ Failed to auto-save to Google Tasks")
            
    else:
        click.echo("❌ Failed to add task")
        logger.error("Failed to add task")
        exit(1)