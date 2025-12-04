#!/usr/bin/env python3
"""
Update command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import TaskStatus, Priority

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.argument('task_id')
@click.option('--title', '-t', help='New task title')
@click.option('--description', '-d', help='New task description')
@click.option('--due', help='New due date (ISO format, e.g., 2024-12-31 or 2024-12-31T15:30:00)')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              help='New task priority')
@click.option('--project', '-p', help='New project name')
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'waiting', 'deleted']), 
              help='New task status')
@click.option('--tags', '-g', help='New task tags (comma-separated, replaces existing tags)')
@click.option('--notes', '-n', help='New task notes')
@click.option('--depends-on', '-D', help='New task dependencies (comma-separated, replaces existing dependencies)')
@click.option('--recurring', '-r', help='New recurrence rule')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def update(ctx, task_id, title, description, due, priority, project, status, tags, notes, depends_on, recurring, account):
    """Update a task"""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    
    # Determine the account to use
    if account:
        account_name = account
    else:
        account_name = ctx.obj.get('account_name')
        
    logger.info(f"Updating task {task_id} {'(Google Tasks)' if use_google_tasks else '(Local)'} for account: {account_name or 'default'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    task_manager = TaskManager(use_google_tasks=use_google_tasks, account_name=account_name)
    
    # Prepare update data
    update_data = {}
    if title:
        update_data['title'] = title
    if description:
        update_data['description'] = description
    if due:
        update_data['due'] = due
    if priority:
        update_data['priority'] = Priority(priority)
    if project:
        update_data['project'] = project
    if status:
        update_data['status'] = TaskStatus(status)
    if tags:
        update_data['tags'] = [tag.strip() for tag in tags.split(',')]
    if notes is not None:  # Allow empty notes to clear the field
        update_data['notes'] = notes
    if depends_on is not None:  # Allow empty dependencies to clear the field
        update_data['dependencies'] = [dep.strip() for dep in depends_on.split(',')]
    if recurring is not None:  # Allow empty recurrence to clear the field
        update_data['recurrence_rule'] = recurring
        update_data['is_recurring'] = bool(recurring)
    
    # Try to update the task
    updated_task = task_manager.update_task(task_id, **update_data)
    
    if updated_task:
        click.echo(f"✅ Task {task_id} updated successfully!")
        
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
            if sync_manager.sync_single_task(updated_task, 'update'):
                 click.echo("✅ Auto-saved to Google Tasks")
            else:
                 click.echo("⚠️ Failed to auto-save to Google Tasks")
    else:
        click.echo(f"❌ Task {task_id} not found!")
        exit(1)