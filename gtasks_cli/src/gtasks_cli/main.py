#!/usr/bin/env python3
"""
Google Tasks CLI - Main Entry Point
"""

import click
import os
from gtasks_cli.commands.add import add
from gtasks_cli.commands.list import list as list_tasks
from gtasks_cli.commands.search import search
from gtasks_cli.commands.view import view
from gtasks_cli.commands.done import done
from gtasks_cli.commands.delete import delete
from gtasks_cli.commands.update import update
from gtasks_cli.commands.sync import sync
from gtasks_cli.commands.auth import auth
from gtasks_cli.commands.summary import summary
from gtasks_cli.commands.interactive import interactive
from gtasks_cli.commands.deduplicate import deduplicate
from gtasks_cli.commands.account import account
from gtasks_cli.commands.advanced_sync import advanced_sync
from gtasks_cli.commands.generate_report import generate_report
from gtasks_cli.commands.config import config
from gtasks_cli.commands.ai import ai
from gtasks_cli.commands.mcp import mcp
from gtasks_cli.utils.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


@click.group()
@click.option('--google', '-g', is_flag=True, help='Use Google Tasks API instead of local storage')
@click.option('--storage', '-s', type=click.Choice(['json', 'sqlite']), default='sqlite', 
              help='Storage backend to use (json or sqlite)')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.option('--auto-save/--no-auto-save', default=None, help='Enable/disable auto-save to Google Tasks')
@click.pass_context
def cli(ctx, google, storage, account, auto_save):
    """Google Tasks CLI - A powerful command line interface for managing tasks."""
    ctx.ensure_object(dict)
    ctx.obj['use_google_tasks'] = google
    ctx.obj['storage_backend'] = storage
    ctx.obj['auto_save'] = auto_save
    
    # Determine the account to use
    if account:
        # Explicitly specified account
        account_name = account
    else:
        # Check for session default
        account_name = os.environ.get('GTASKS_DEFAULT_ACCOUNT')
        if not account_name:
            # Check for global default
            from gtasks_cli.storage.config_manager import ConfigManager
            config = ConfigManager.get_global_config()
            account_name = config.get('default_account')
    
    ctx.obj['account_name'] = account_name
    
    # Set environment variable for account-specific configuration
    if account_name:
        config_dir = os.path.join(os.path.expanduser("~"), ".gtasks", account_name)
        os.environ['GTASKS_CONFIG_DIR'] = config_dir
        logger.debug(f"Using account '{account_name}' with config directory: {config_dir}")
    elif 'GTASKS_CONFIG_DIR' in os.environ:
        # Clear the environment variable if no account specified
        del os.environ['GTASKS_CONFIG_DIR']
    
    logger.debug(f"CLI initialized with google={google}, storage={storage}, account={account_name}")


# Register commands
cli.add_command(add)
cli.add_command(list_tasks)
cli.add_command(search)
cli.add_command(view)
cli.add_command(done)
cli.add_command(delete)
cli.add_command(update)
cli.add_command(sync)
cli.add_command(auth)
cli.add_command(summary)
cli.add_command(interactive)
cli.add_command(deduplicate)
cli.add_command(account)
cli.add_command(advanced_sync)
cli.add_command(generate_report)
cli.add_command(config)
cli.add_command(ai)
cli.add_command(mcp)


def main():
    """Main entry point for the CLI application."""
    cli()


if __name__ == '__main__':
    main()