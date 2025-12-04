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
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def delete(ctx, task_id, account):
    """Delete a task"""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    
    # Determine the account to use
    if account:
        account_name = account
    else:
        account_name = ctx.obj.get('account_name')
        
    logger.info(f"Deleting task {task_id} {'(Google Tasks)' if use_google_tasks else '(Local)'} for account: {account_name or 'default'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    task_manager = TaskManager(use_google_tasks=use_google_tasks, account_name=account_name)
    
    # Get task first for auto-save
    task = task_manager.get_task(task_id)
    if not task:
        click.echo(f"❌ Task {task_id} not found!")
        exit(1)
    
    # Try to delete the task (mark as deleted)
    if task_manager.delete_task(task_id):
        click.echo(f"🗑️ Task {task_id} deleted!")
        
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
            if sync_manager.sync_single_task(task, 'delete'):
                 click.echo("✅ Auto-saved to Google Tasks")
            else:
                 click.echo("⚠️ Failed to auto-save to Google Tasks")
    else:
        click.echo(f"❌ Failed to delete task {task_id}!")
        exit(1)