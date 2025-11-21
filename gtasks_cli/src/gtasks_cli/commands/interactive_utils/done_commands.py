#!/usr/bin/env python3
"""
Done command functionality for interactive mode
"""

import click
from gtasks_cli.models.task import TaskStatus


def handle_done_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """Handle the done command in interactive mode"""
    if len(command_parts) < 2:
        click.echo("Usage: done <task_number>")
        return
    
    try:
        task_num = int(command_parts[1])
        task = task_state.get_task_by_number(task_num)
        if task:
            # Mark task as completed
            success = task_manager.update_task(task.id, status=TaskStatus.COMPLETED)
            if success:
                click.echo(f"Task '{task.title}' marked as completed.")
                # Instead of refreshing the whole list, just remove the task from current view
                _remove_task_from_state(task_state, task.id)
            else:
                click.echo("Failed to mark task as completed.")
        else:
            click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.tasks)}.")
    except ValueError:
        click.echo("Invalid task number. Please enter a valid integer.")


def _remove_task_from_state(task_state, task_id):
    """Remove a task from the task state instead of refreshing the entire list"""
    # Remove the task from the list
    task_state.tasks = [task for task in task_state.tasks if task.id != task_id]
    
    # Refresh the mappings
    task_state.task_number_to_id = {}
    task_state.task_id_to_number = {}
    for i, task in enumerate(task_state.tasks, 1):
        task_state.task_number_to_id[i] = task.id
        task_state.task_id_to_number[task.id] = i