#!/usr/bin/env python3
"""
Update command functionality for interactive mode
"""

import click
import tempfile
import os
import subprocess
from typing import Optional
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_update_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """Handle the update command in interactive mode"""
    if len(command_parts) < 2:
        task_num_input = click.prompt("  Which task number to update? (Enter/c to cancel)", default="c", show_default=False).strip()
        if not task_num_input or task_num_input.lower() in ['c', 'cancel', 'q', 'exit']:
            return
        command_parts = ['update', task_num_input]
    
    try:
        task_num = int(command_parts[1])
        use_editor = '--editor' in command_parts or '-e' in command_parts
        task = task_state.get_task_by_number(task_num)
        if task:
            if use_editor:
                # Use external editor for editing task
                # Capture original state
                original_title = task.title
                original_description = task.description
                original_notes = task.notes
                original_spaces = getattr(task, 'spaces', {})
                
                updated_task = _edit_task_in_editor(task, task_manager)
                if updated_task:
                    click.echo(f"Task '{updated_task.title}' updated successfully with editor.")
                    
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
                        if sync_manager.sync_single_task(updated_task, 'update'):
                             click.echo("✅ Auto-saved to Google Tasks")
                        else:
                             click.echo("⚠️ Failed to auto-save to Google Tasks")
                    
                    # Register undo operation
                    from gtasks_cli.commands.interactive_utils.undo_manager import undo_manager
                    
                    def undo_editor_update():
                        try:
                            task_manager.update_task(
                                task.id,
                                title=original_title,
                                description=original_description,
                                notes=original_notes,
                                spaces=original_spaces,
                            )
                            # Update in-memory task
                            for t in task_state.tasks:
                                if t.id == task.id:
                                    t.title = original_title
                                    t.description = original_description
                                    t.notes = original_notes
                                    t.spaces = original_spaces
                                    break
                            return True
                        except Exception as e:
                            logger.error(f"Undo editor update failed: {e}")
                            return False

                    undo_manager.push_operation(
                        description=f"Update task '{original_title}' (editor)",
                        undo_func=undo_editor_update
                    )
                    
                    # Refresh the specific task in the task list instead of full refresh
                    _update_single_task_in_state(task_state, updated_task)
                else:
                    click.echo("Task update cancelled or failed.")
            else:
                from rich.console import Console
                from gtasks_cli.models.task import Priority
                from gtasks_cli.utils.space_extractor import (
                    split_notes_and_metadata,
                    combine_notes_and_metadata,
                    parse_spaces_input,
                    format_spaces_for_input,
                )

                console = Console()
                raw_notes = task.description or task.notes or ""
                clean_notes, current_tags, current_spaces = split_notes_and_metadata(raw_notes)
                if not current_spaces and getattr(task, 'spaces', None):
                    current_spaces = task.spaces
                if not current_tags and getattr(task, 'tags', None):
                    current_tags = task.tags

                console.print(f"\n[bold cyan]✏️  Update Task: {task.title}[/bold cyan]")
                console.print("  [1] Title")
                console.print("  [2] Description / Notes")
                console.print("  [3] Due Date")
                console.print("  [4] Priority")
                console.print("  [5] Spaces")
                console.print("  [6] Tags")
                console.print("  [7] All fields (Guided)")
                console.print("  [c] Cancel")
                
                choice = click.prompt("  Select field to update", default="7", show_default=False).strip().lower()
                if choice in ['c', 'cancel', 'q', 'exit']:
                    return

                new_title = task.title
                new_desc = clean_notes
                new_spaces = current_spaces
                new_tags = current_tags
                new_due = task.due
                new_priority = task.priority

                if choice in ['1', '7']:
                    new_title = click.prompt("  📝 Task title", default=task.title)

                if choice in ['2', '7']:
                    new_desc = click.prompt("  📄 Task description/notes", default=clean_notes)

                if choice in ['3', '7']:
                    from datetime import datetime, timedelta
                    from dateutil import parser as date_parser
                    console.print("  📅 Due date: [1] Today  [2] Tomorrow  [3] In 3 days  [4] Next week  [5] Clear  [Enter] Keep")
                    due_choice = click.prompt("     Select (1-5) or type date", default="", show_default=False).strip()
                    if due_choice == "1":
                        new_due = datetime.now()
                    elif due_choice == "2":
                        new_due = datetime.now() + timedelta(days=1)
                    elif due_choice == "3":
                        new_due = datetime.now() + timedelta(days=3)
                    elif due_choice == "4":
                        new_due = datetime.now() + timedelta(days=7)
                    elif due_choice == "5":
                        new_due = None
                    elif due_choice:
                        try:
                            new_due = date_parser.parse(due_choice)
                        except Exception:
                            console.print("     [yellow]Could not parse date, keeping current.[/yellow]")

                if choice in ['4', '7']:
                    console.print("  ⚡ Priority: [1] Low  [2] Medium  [3] High  [4] Critical")
                    prio_choice = click.prompt("     Select (1-4)", default="", show_default=False).strip()
                    prio_map = {"1": Priority.LOW, "2": Priority.MEDIUM, "3": Priority.HIGH, "4": Priority.CRITICAL}
                    if prio_choice in prio_map:
                        new_priority = prio_map[prio_choice]

                if choice in ['5', '7']:
                    default_spaces_str = format_spaces_for_input(current_spaces)
                    spaces_input = click.prompt("  🌌 Spaces (e.g. work:frontend, personal)", default=default_spaces_str)
                    new_spaces = parse_spaces_input(spaces_input)

                if choice in ['6', '7']:
                    default_tags_str = ", ".join(current_tags) if current_tags else ""
                    tags_input = click.prompt("  🏷️  Tags (e.g. urgent, backend)", default=default_tags_str)
                    new_tags = [t.strip().lstrip('#') for t in tags_input.split(',') if t.strip()]

                combined_desc = combine_notes_and_metadata(new_desc or "", tags=new_tags or None, spaces=new_spaces or None)

                # Capture original state
                original_title = task.title
                original_description = task.description
                original_notes = task.notes
                original_spaces = getattr(task, 'spaces', {})
                original_tags = getattr(task, 'tags', [])
                original_due = task.due
                original_priority = task.priority

                # Update the task
                update_kwargs = {
                    'title': new_title,
                    'description': combined_desc,
                    'notes': combined_desc,
                    'spaces': new_spaces,
                    'tags': new_tags,
                    'due': new_due,
                    'priority': new_priority,
                }
                update_success = task_manager.update_task(task.id, **update_kwargs)
                if update_success:
                    click.echo(f"Task '{title}' updated successfully.")
                    
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
                        updated_task_obj = task_manager.get_task(task.id)
                        if updated_task_obj:
                            from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager
                            click.echo("Auto-saving to Google Tasks...")
                            sync_manager = AdvancedSyncManager(task_manager.storage, task_manager.google_client)
                            if sync_manager.sync_single_task(updated_task_obj, 'update'):
                                 click.echo("✅ Auto-saved to Google Tasks")
                            else:
                                 click.echo("⚠️ Failed to auto-save to Google Tasks")
                    
                    # Register undo operation
                    from gtasks_cli.commands.interactive_utils.undo_manager import undo_manager
                    
                    def undo_update():
                        try:
                            task_manager.update_task(
                                task.id,
                                title=original_title,
                                description=original_description,
                                notes=original_notes,
                                spaces=original_spaces,
                            )
                            # Update in-memory task
                            for t in task_state.tasks:
                                if t.id == task.id:
                                    t.title = original_title
                                    t.description = original_description
                                    t.notes = original_notes
                                    t.spaces = original_spaces
                                    break
                            return True
                        except Exception as e:
                            logger.error(f"Undo update failed: {e}")
                            return False

                    undo_manager.push_operation(
                        description=f"Update task '{original_title}'",
                        undo_func=undo_update
                    )

                    # Just update the specific task in our current view instead of refreshing everything
                    # Get the updated task and update it in place
                    updated_tasks = task_manager.list_tasks()
                    for updated_task in updated_tasks:
                        if updated_task.id == task.id:
                            _update_single_task_in_state(task_state, updated_task)
                            break
                else:
                    click.echo("Failed to update task.")
        else:
            click.echo(f"Invalid task number. Please enter a number between 1 and {len(task_state.tasks)}.")
    except ValueError:
        click.echo("Invalid task number. Please enter a valid integer.")


def _update_single_task_in_state(task_state, updated_task):
    """Update a single task in the task state instead of refreshing the entire list"""
    # Find and update the task in place
    for i, task in enumerate(task_state.tasks):
        if task.id == updated_task.id:
            task_state.tasks[i] = updated_task
            break
    # Refresh the mappings
    task_state.task_number_to_id = {}
    task_state.task_id_to_number = {}
    for i, task in enumerate(task_state.tasks, 1):
        task_state.task_number_to_id[i] = task.id
        task_state.task_id_to_number[task.id] = i


def _refresh_task_list(task_manager, task_state):
    """Refresh the task list with incomplete tasks only"""
    tasks = task_manager.list_tasks()
    incomplete_tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
    
    # Add list_title to each task for grouping display (default to "Tasks" for local mode)
    for task in incomplete_tasks:
        if not hasattr(task, 'list_title') or not task.list_title:
            task.list_title = "Tasks"
    
    # Note: We need to import these functions, will handle this when we restructure
    # display_tasks_grouped_by_list(incomplete_tasks)
    task_state.set_tasks(incomplete_tasks)


def _edit_task_in_editor(task: Task, task_manager) -> Optional[Task]:
    """Edit a task in an external editor.
    
    Args:
        task: The task to edit
        task_manager: The task manager instance
        
    Returns:
        Updated task if successful, None if cancelled or failed
    """
    # Create a temporary file with task content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        # Write task content to the temporary file
        temp_file.write(f"# Editing Task: {task.title}\n\n")
        temp_file.write("## Instructions\n")
        temp_file.write("# - Modify the title after the 'Title:' marker\n")
        temp_file.write("# - Modify the description after the 'Description:' marker\n")
        temp_file.write("# - Lines starting with '#' are comments and will be ignored\n")
        temp_file.write("# - Save and exit the editor to apply changes\n")
        temp_file.write("# - Close the editor without saving to cancel\n\n")
        temp_file.write(f"Title: {task.title}\n\n")
        temp_file.write("Description:\n")
        
        # Combine description and notes for the editor content
        editor_content = ""
        if task.description:
            editor_content += task.description
        if task.notes:
            if editor_content:
                editor_content += "\n"
            editor_content += task.notes
            
        if editor_content:
            # Add the content with proper indentation
            for line in editor_content.split('\n'):
                temp_file.write(f"{line}\n")
        temp_file.flush()
        
        # Get editor from environment or use default
        editor = os.environ.get('EDITOR', 'vim')
        
        try:
            # Open the file in the editor
            result = subprocess.run([editor, temp_file.name])
            
            # If editor was closed successfully, read the updated content
            if result.returncode == 0:
                with open(temp_file.name, 'r') as updated_file:
                    content = updated_file.read()
                
                # Parse the updated content
                lines = content.split('\n')
                title = task.title  # Default to original title
                description_lines = []
                in_description = False
                
                for line in lines:
                    # Skip comment lines
                    if line.startswith('#'):
                        continue
                    
                    # Check for title line
                    if line.startswith('Title:'):
                        title = line[6:].strip()  # Remove 'Title:' prefix
                    # Check for description section
                    elif line == 'Description:':
                        in_description = True
                    elif in_description:
                        # Collect description lines
                        description_lines.append(line)
                
                # Clean up description (remove trailing empty lines)
                while description_lines and not description_lines[-1].strip():
                    description_lines.pop()
                
                description = '\n'.join(description_lines) if description_lines else None
                
                from gtasks_cli.utils.space_extractor import split_notes_and_metadata
                clean_desc, _, spaces = split_notes_and_metadata(description or "")

                # Update the task
                update_result = task_manager.update_task(
                    task.id, 
                    title=title, 
                    description=description,
                    notes=description,
                    spaces=spaces
                )
                
                if update_result:
                    # If update was successful, retrieve and return the updated task
                    updated_tasks = task_manager.list_tasks()
                    for updated_task in updated_tasks:
                        if updated_task.id == task.id:
                            return updated_task
                    # If we can't find the task, return None
                    return None
                else:
                    # Update failed
                    return None
            else:
                # Editor was not closed successfully (e.g., killed)
                return None
                
        except FileNotFoundError:
            click.echo(f"Editor '{editor}' not found. Please set the EDITOR environment variable to a valid editor.")
            return None
        except Exception as e:
            click.echo(f"Error editing task: {e}")
            logger.error(f"Error editing task {task.id}: {e}")
            return None
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")