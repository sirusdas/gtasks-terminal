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
            # Confirm deletion
            confirm = click.confirm(f"Are you sure you want to delete task '{task.title}'?")
            if confirm:
                # Capture original status for undo
                original_status = task.status
                
                success = task_manager.delete_task(task.id)
                if success:
                    click.echo(f"Task '{task.title}' deleted successfully.")
                    
                    # Auto-save (CLI option overrides config)
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
                        if sync_manager.sync_single_task(task, 'delete'):
                             click.echo("✅ Auto-saved to Google Tasks")
                        else:
                             click.echo("⚠️ Failed to auto-save to Google Tasks")
                    
                    # Register undo operation
                    from gtasks_cli.commands.interactive_utils.undo_manager import undo_manager
                    
                    def undo_delete():
                        try:
                            # Restore status (undelete)
                            task_manager.update_task(task.id, status=original_status)
                            return True
                        except Exception as e:
                            logger.error(f"Undo delete failed: {e}")
                            return False

                    undo_manager.push_operation(
                        description=f"Delete task '{task.title}'",
                        undo_func=undo_delete
                    )
                    
                    # Instead of refreshing the whole list, just remove the task from current view
                    _remove_task_from_state(task_state, task.id)
                else:
                    click.echo("Failed to delete task.")
            else:
                click.echo("Deletion cancelled.")
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