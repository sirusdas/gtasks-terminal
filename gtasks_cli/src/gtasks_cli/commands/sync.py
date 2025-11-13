#!/usr/bin/env python3
"""
Sync command for the Google Tasks CLI application.
"""

import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.core.task_manager import TaskManager

logger = setup_logger(__name__)


@click.command()
@click.pass_context
def sync(ctx):
    """Synchronize tasks between local storage and Google Tasks."""
    storage_backend = ctx.obj.get('storage_backend', 'json')
    
    logger.info(f"Synchronizing with Google Tasks using {storage_backend} storage backend")
    
    # Create task manager with Google Tasks enabled and the selected storage backend
    task_manager = TaskManager(use_google_tasks=True, storage_backend=storage_backend)
    
    # Perform synchronization
    success = task_manager.sync_with_google_tasks()
    
    if success:
        click.echo("✅ Synchronization with Google Tasks completed successfully!")
        logger.info("Synchronization completed successfully")
    else:
        click.echo("❌ Failed to synchronize with Google Tasks!")
        logger.error("Synchronization failed")
        exit(1)