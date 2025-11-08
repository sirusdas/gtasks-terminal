#!/usr/bin/env python3
"""
Google Tasks CLI - Main Entry Point
"""

import click
import os
import json
from datetime import datetime
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Priority

# Import commands
from gtasks_cli.commands.add import add
from gtasks_cli.commands.list import list as list_cmd
from gtasks_cli.commands.search import search
from gtasks_cli.commands.deduplicate import deduplicate
from gtasks_cli.commands.view import view
from gtasks_cli.commands.done import done
from gtasks_cli.commands.delete import delete
from gtasks_cli.commands.update import update
from gtasks_cli.commands.sync import sync
from gtasks_cli.commands.auth import auth
from gtasks_cli.commands.summary import summary
from gtasks_cli.commands.interactive import interactive

# Set up logger
logger = setup_logger(__name__)


@click.group()
@click.version_option(version='0.1.0')
@click.option('--config', type=click.Path(), help='Config file path')
@click.option('--verbose', '-v', count=True, help='Verbose output')
@click.option('--google', '-g', is_flag=True, help='Use Google Tasks API instead of local storage')
@click.pass_context
def cli(ctx, config, verbose, google):
    """Google Tasks CLI with superpowers ⚡

    A powerful command-line interface for managing Google Tasks with advanced features
    like task dependencies, recurrence, projects, tags, and synchronization.
    
    \b
    Examples:
      # Add a simple task
      gtasks add -t "Buy groceries"
      
      # Add a task with due date and priority
      gtasks add -t "Finish report" --due "2024-12-31" --priority high
      
      # List all pending tasks
      gtasks list --status pending
      
      # Search for tasks
      gtasks search "report"
      
      # Mark task as completed
      gtasks done <task-id>
      
      # Start interactive mode
      gtasks interactive
      
      # Use Google Tasks API
      gtasks --google list
    """
    # Store context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['CONFIG'] = config
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['USE_GOOGLE_TASKS'] = google
    
    # Set up logging based on verbosity
    if verbose >= 2:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose >= 1:
        import logging
        logging.getLogger().setLevel(logging.INFO)


# Register commands
cli.add_command(add)
cli.add_command(list_cmd)
cli.add_command(search)
cli.add_command(deduplicate)
cli.add_command(view)
cli.add_command(done)
cli.add_command(delete)
cli.add_command(update)
cli.add_command(sync)
cli.add_command(auth)
cli.add_command(summary)
cli.add_command(interactive)


def main():
    """Main entry point for the application"""
    cli()


if __name__ == '__main__':
    main()