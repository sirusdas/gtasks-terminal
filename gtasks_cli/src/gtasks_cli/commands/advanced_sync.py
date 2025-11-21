#!/usr/bin/env python3
"""
Advanced Sync command for the Google Tasks CLI application.
"""

import click
import os
import traceback
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.storage.config_manager import ConfigManager

logger = setup_logger(__name__)


@click.command()
@click.option('--push', is_flag=True, help='Push local changes to Google Tasks only')
@click.option('--pull', is_flag=True, help='Pull changes from Google Tasks only')
@click.option('--all', 'sync_all', is_flag=True, help='Perform full sync instead of incremental sync')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def advanced_sync(ctx, push, pull, sync_all, account):
    """Advanced synchronization between local storage and Google Tasks with push/pull options."""
    storage_backend = ctx.obj.get('storage_backend', 'json')
    
    # Determine the account to use
    if account:
        # Explicitly specified account
        account_name = account
    else:
        # Check context object for account
        account_name = ctx.obj.get('account_name')
    
    logger.info(f"Advanced synchronization with Google Tasks using {storage_backend} storage backend for account: {account_name or 'default'}")
    
    # Load configuration to get sync settings
    config_manager = ConfigManager(account_name=account_name)
    pull_range_days = config_manager.get('sync.pull_range_days')
    
    # If --all is specified, set pull_range_days to None to perform full sync
    if sync_all:
        pull_range_days = None
        logger.info("Full sync mode enabled (--all)")
    
    # Create task manager with Google Tasks enabled, the selected storage backend, and account
    task_manager = TaskManager(use_google_tasks=True, storage_backend=storage_backend, account_name=account_name)
    
    # Get the Google client and storage from the task manager
    google_client = task_manager.google_client
    storage = task_manager.storage
    
    # Create advanced sync manager with pull_range_days configuration
    sync_manager = AdvancedSyncManager(storage, google_client, pull_range_days=pull_range_days)
    
    success = False
    if push and not pull:
        # Push only
        logger.info("Performing push-only synchronization")
        success = sync_manager.push_to_google()
        if success:
            if account_name:
                click.echo(f"✅ Push to Google Tasks completed successfully for account '{account_name}'!")
            else:
                click.echo("✅ Push to Google Tasks completed successfully!")
        else:
            if account_name:
                click.echo(f"❌ Failed to push to Google Tasks for account '{account_name}'!")
            else:
                click.echo("❌ Failed to push to Google Tasks!")
    elif pull and not push:
        # Pull only
        logger.info("Performing pull-only synchronization")
        success = sync_manager.pull_from_google()
        if success:
            if account_name:
                click.echo(f"✅ Pull from Google Tasks completed successfully for account '{account_name}'!")
            else:
                click.echo("✅ Pull from Google Tasks completed successfully!")
        else:
            if account_name:
                click.echo(f"❌ Failed to pull from Google Tasks for account '{account_name}'!")
            else:
                click.echo("❌ Failed to pull from Google Tasks!")
    elif not push and not pull:
        # Bidirectional sync (default)
        logger.info("Performing bidirectional synchronization")
        success = sync_manager.sync()
        if success:
            if account_name:
                click.echo(f"✅ Bidirectional synchronization with Google Tasks completed successfully for account '{account_name}'!")
            else:
                click.echo("✅ Bidirectional synchronization with Google Tasks completed successfully!")
        else:
            if account_name:
                click.echo(f"❌ Failed to synchronize with Google Tasks for account '{account_name}'!")
            else:
                click.echo("❌ Failed to synchronize with Google Tasks!")
    else:
        # Both push and pull specified (same as bidirectional)
        logger.info("Both push and pull specified, performing bidirectional synchronization")
        success = sync_manager.sync()
        if success:
            if account_name:
                click.echo(f"✅ Bidirectional synchronization with Google Tasks completed successfully for account '{account_name}'!")
            else:
                click.echo("✅ Bidirectional synchronization with Google Tasks completed successfully!")
        else:
            if account_name:
                click.echo(f"❌ Failed to synchronize with Google Tasks for account '{account_name}'!")
            else:
                click.echo("❌ Failed to synchronize with Google Tasks!")