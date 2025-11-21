#!/usr/bin/env python3
"""
Add command functionality for interactive mode
"""

import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.commands.interactive_utils.common import refresh_task_list

logger = setup_logger(__name__)


def handle_add_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """Handle the add command in interactive mode"""
    # Collect task details
    title = click.prompt("Task title")
    description = click.prompt("Task description", default="")
    if description == "":
        description = None
    
    # Add the task
    task = task_manager.add_task(title=title, description=description)
    if task:
        click.echo(f"Task '{title}' added successfully.")
        # Refresh task list - only show incomplete tasks and maintain grouped display
        refresh_task_list(task_manager, task_state, use_google_tasks)
    else:
        click.echo("Failed to add task.")