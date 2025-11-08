#!/usr/bin/env python3
"""
Sync command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.pass_context
def sync(ctx):
    """Synchronize tasks with Google Tasks"""
    use_offline = ctx.obj.get('OFFLINE_MODE', False)
    
    if use_offline:
        logger.info("Synchronization skipped - Offline mode enabled")
        click.echo("🚫 Cannot synchronize: Offline mode is active")
        return
    
    logger.info("Synchronizing with Google Tasks")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    # Create task manager with Google Tasks enabled
    task_manager = TaskManager(use_google_tasks=True)
    
    try:
        if task_manager.sync_with_google_tasks():
            click.echo("✅ Synchronization with Google Tasks completed successfully!")
        else:
            click.echo("❌ Failed to synchronize with Google Tasks!")
            exit(1)
    except Exception as e:
        logger.error(f"Synchronization error: {e}")
        click.echo(f"❌ Synchronization error: {str(e)}")
        exit(1)