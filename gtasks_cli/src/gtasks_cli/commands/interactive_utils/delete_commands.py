#!/usr/bin/env python3
"""
Delete command functionality for interactive mode
"""

import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.commands.interactive_utils.common import refresh_task_list

logger = setup_logger(__name__)


def handle_delete_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """Handle the delete command in interactive mode"""
    if len(command_parts) < 2:
        click.echo("Usage: delete <task_number>")
        return
        
    try:
        task_num = int(command_parts[1])
        task = task_state.get_task_by_number(task_num)
        if task:
            confirm = click.confirm(f"Are you sure you want to delete task '{task.title}'?")
            if confirm:
                if task_manager.delete_task(task.id):
                    click.echo(f"Task '{task.title}' deleted.")
                    # Refresh task list - only show incomplete tasks
                    refresh_task_list(task_manager, task_state, use_google_tasks)
                else:
                    click.echo("Failed to delete task.")
        else:
            click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.tasks)}.")
    except ValueError:
        click.echo("Invalid task number. Please enter a valid integer.")