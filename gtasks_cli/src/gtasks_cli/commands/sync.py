#!/usr/bin/env python3
"""
Sync command for the Google Tasks CLI application.
"""

import click
import os
import traceback
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.core.task_manager import TaskManager

logger = setup_logger(__name__)


@click.command()
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def sync(ctx, account):
    """Synchronize tasks between local storage and Google Tasks."""
    storage_backend = ctx.obj.get('storage_backend', 'json')
    
    # Determine the account to use
    if account:
        # Explicitly specified account
        account_name = account
    else:
        # Check context object for account
        account_name = ctx.obj.get('account_name')
    
    logger.info(f"Synchronizing with Google Tasks using {storage_backend} storage backend for account: {account_name or 'default'}")
    
    # Create task manager with Google Tasks enabled, the selected storage backend, and account
    task_manager = TaskManager(use_google_tasks=True, storage_backend=storage_backend, account_name=account_name)
    
    # Perform synchronization
    success = task_manager.sync_with_google_tasks()
    
    if success:
        if account_name:
            click.echo(f"✅ Synchronization with Google Tasks completed successfully for account '{account_name}'!")
        else:
            click.echo("✅ Synchronization with Google Tasks completed successfully!")
        logger.info("Synchronization completed successfully")
    else:
        if account_name:
            click.echo(f"❌ Failed to synchronize with Google Tasks for account '{account_name}'!")
        else:
            click.echo("❌ Failed to synchronize with Google Tasks!")
        logger.error("Synchronization failed")
        # Print more detailed error information
        click.echo("For more details, check the logs or run with increased verbosity.")
        exit(1)