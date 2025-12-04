#!/usr/bin/env python3
"""
Add command functionality for interactive mode
"""

import click
from gtasks_cli.models.task import Task, TaskStatus, Priority


def handle_add_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """Handle the add command in interactive mode"""
    # Collect task details
    title = click.prompt("Task title")
    description = click.prompt("Task description", default="")
    if description == "":
        description = None
    
    # Create the task
    task = Task(
        title=title,
        description=description,
        status=TaskStatus.PENDING,
        priority=Priority.MEDIUM
    )
    
    # Add the task
    added_task = task_manager.add_task(task)
    if added_task:
        click.echo(f"Task '{added_task.title}' added successfully.")
        
        # Register undo operation
        from gtasks_cli.commands.interactive_utils.undo_manager import undo_manager
        
        def undo_add():
            try:
                task_manager.delete_task(added_task.id)
                return True
            except Exception as e:
                click.echo(f"Undo add failed: {e}")
                return False

        undo_manager.push_operation(
            description=f"Add task '{added_task.title}'",
            undo_func=undo_add
        )
        
        # Instead of refreshing the whole list, just add the new task to current view
        _add_task_to_state(task_state, added_task)
    else:
        click.echo("Failed to add task.")


def _add_task_to_state(task_state, new_task):
    """Add a new task to the task state instead of refreshing the entire list"""
    # Add the task to the list
    task_state.tasks.append(new_task)
    
    # Refresh the mappings
    task_state.task_number_to_id = {}
    task_state.task_id_to_number = {}
    for i, task in enumerate(task_state.tasks, 1):
        task_state.task_number_to_id[i] = task.id
        task_state.task_id_to_number[task.id] = i