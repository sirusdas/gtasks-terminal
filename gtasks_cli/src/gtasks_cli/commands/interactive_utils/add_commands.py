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
        
        # Check for auto-save (CLI option overrides config)
        from gtasks_cli.storage.config_manager import ConfigManager
        config_manager = ConfigManager(account_name=task_manager.account_name)
        cli_auto_save = getattr(task_manager, 'cli_auto_save', None)
        
        # Use CLI option if provided, otherwise use config
        if cli_auto_save is not None:
            auto_save = cli_auto_save
        else:
            auto_save = config_manager.get('sync.auto_save', False)
        
        if not use_google_tasks and auto_save:
            from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager
            click.echo("Auto-saving to Google Tasks...")
            sync_manager = AdvancedSyncManager(task_manager.storage, task_manager.google_client)
            if sync_manager.sync_single_task(added_task, 'create', old_task_id=added_task.id):
                 click.echo("✅ Auto-saved to Google Tasks")
            else:
                 click.echo("⚠️ Failed to auto-save to Google Tasks")
        
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