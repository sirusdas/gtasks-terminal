import click
import re
from typing import List, Dict, Any, Tuple
from gtasks_cli.models.task import Task
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

def handle_update_tags_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """
    Handle the update-tags command.
    Syntax:
    update-tags DEL[1,2,3|sirus],ADD[4,5,6|today]
    update-tags ADD[1,2|work,sirus] - Add multiple tags to tasks
    update-tags DEL[3|personal,sirus] - Remove multiple tags from task
    update-tags ADD[sirus] --all
    update-tags ALL[ADD:urgent,sirus] - Add tags to all tasks
    update-tags ALL[DEL:old,done] - Remove tags from all tasks
    update-tags ALL[ADD:new],ALL[DEL:old] - Combined operations on all tasks
    """
    if len(command_parts) < 2:
        click.echo("Usage: update-tags DEL[ids|tag1,tag2],ADD[ids|tag1,tag2] or update-tags ALL[ADD:tag1,tag2]")
        return

    # Join parts to handle spaces
    full_args = " ".join(command_parts[1:])
    
    # Check for --all flag (legacy support)
    apply_to_all = False
    if "--all" in full_args:
        apply_to_all = True
        full_args = full_args.replace("--all", "").strip()

    # Regex to find ALL operations: ALL\[(ADD|DEL):(.*?)\]
    all_ops = re.findall(r'ALL\[(ADD|DEL):(.*?)\]', full_args)
    
    # Regex to find regular operations: (ADD|DEL)\[(.*?)\]
    # But exclude ALL[...] patterns by using negative lookbehind
    regular_ops = re.findall(r'(?<!ALL\[)(ADD|DEL)\[(.*?)\]', full_args)
    
    if not all_ops and not regular_ops:
        click.echo("Invalid format. Use ADD[ids|tag1,tag2], ALL[ADD:tag1,tag2], or ALL[DEL:tag1,tag2].")
        return

    tasks_to_update = {} # Map task_id -> task object
    updates = [] # List of (task_id, operation, tag)

    # Process ALL operations first
    for op_type, tags_part in all_ops:
        tags = [t.strip() for t in tags_part.split(',') if t.strip()]
        
        if not tags:
            click.echo("Error: Empty tag specified in ALL operation.")
            continue
        
        # Apply to all tasks in current list
        for task in task_state.tasks:
            tasks_to_update[task.id] = task
            for tag in tags:
                updates.append((task.id, op_type, tag))

    # Process regular operations
    for op_type, content in regular_ops:
        tags = []
        target_task_ids = []
        
        if '|' in content:
            ids_part, tags_part = content.split('|', 1)
            # Parse multiple tags separated by commas
            tags = [t.strip() for t in tags_part.split(',') if t.strip()]
            ids_str = ids_part.strip()
            
            if ids_str:
                try:
                    # Handle comma separated, replace . with , for typo tolerance
                    ids_str = ids_str.replace('.', ',') 
                    indices = [int(x.strip()) for x in ids_str.split(',') if x.strip()]
                    
                    for idx in indices:
                        task = task_state.get_task_by_number(idx)
                        if task:
                            target_task_ids.append(task.id)
                            tasks_to_update[task.id] = task
                        else:
                            click.echo(f"Warning: Task number {idx} not found.")
                except ValueError:
                    click.echo(f"Invalid ID format in {ids_str}")
                    continue
        else:
            # No pipe, content is tag(s)
            tags = [t.strip() for t in content.split(',') if t.strip()]
            if apply_to_all:
                for task in task_state.tasks:
                    target_task_ids.append(task.id)
                    tasks_to_update[task.id] = task
            else:
                 click.echo(f"Error: No IDs provided for tag(s) '{', '.join(tags)}' and --all not specified.")
                 continue

        if not tags:
            click.echo("Error: Empty tag specified.")
            continue

        # Create updates for each task-tag combination
        for tid in target_task_ids:
            for tag in tags:
                updates.append((tid, op_type, tag))

    if not updates:
        click.echo("No updates to perform.")
        return

    # Group updates by task_id
    task_updates = {} # task_id -> list of (op_type, tag)
    for tid, op, tag in updates:
        if tid not in task_updates:
            task_updates[tid] = []
        task_updates[tid].append((op, tag))
        
    updated_count = 0
    updated_tasks_list = []
    changes_log = []  # Track changes for feedback
    undo_data = [] # List of (task_id, original_notes) for undo
    
    with click.progressbar(task_updates.items(), label="Updating tags", length=len(task_updates)) as bar:
        for tid, ops_list in bar:
            task = tasks_to_update[tid]
            original_notes = task.notes or ""
            current_notes = original_notes
            
            task_changes = []
            modified = False
            for op, tag in ops_list:
                tag_marker = f"[{tag}]"
                if op == 'ADD':
                    if tag_marker not in current_notes:
                        if current_notes:
                            current_notes += f" {tag_marker}"
                        else:
                            current_notes = tag_marker
                        modified = True
                        task_changes.append(f"Added [{tag}]")
                elif op == 'DEL':
                    if tag_marker in current_notes:
                        # Remove tag, handle potential spacing issues
                        # Simple replace might leave double spaces
                        current_notes = current_notes.replace(tag_marker, "")
                        # Clean up extra spaces
                        current_notes = re.sub(r'\s+', ' ', current_notes).strip()
                        modified = True
                        task_changes.append(f"Removed [{tag}]")
            
            if modified:
                try:
                    logger.debug(f"Updating task {task.id}: original_notes='{original_notes}', new_notes='{current_notes}'")
                    task_manager.update_task(task.id, notes=current_notes)
                    task.notes = current_notes
                    
                    # Get fresh task for auto-save
                    updated_task_obj = task_manager.get_task(task.id)
                    if updated_task_obj:
                        updated_tasks_list.append(updated_task_obj)
                        
                    logger.debug(f"After update, task.notes='{task.notes}'")
                    updated_count += 1
                    undo_data.append((task.id, original_notes))
                    
                    task_num = task_state.get_number_by_task_id(task.id) if task_state else "?"
                    task_title = task.title[:40] + "..." if len(task.title) > 40 else task.title
                    changes_log.append(f"  Task #{task_num} ({task_title}): {', '.join(task_changes)}")
                    changes_log.append(f"    Notes now: '{current_notes}'")
                except Exception as e:
                    logger.error(f"Failed to update task {task.id}: {e}")
                    click.echo(f"\nFailed to update task {task.title}: {e}")

    # Register undo operation if changes were made
    if undo_data:
        from gtasks_cli.commands.interactive_utils.undo_manager import undo_manager
        
        def undo_func():
            success_count = 0
            for tid, notes in undo_data:
                try:
                    # Update database
                    task_manager.update_task(tid, notes=notes)
                    # Update in-memory task if available in current state
                    if task_state:
                        # We need to find the task in the current state
                        # It might be different from the one we have a reference to if state changed
                        for t in task_state.tasks:
                            if t.id == tid:
                                t.notes = notes
                                break
                    success_count += 1
                except Exception as e:
                    logger.error(f"Undo failed for task {tid}: {e}")
            
            click.echo(f"Undid tag updates for {success_count} tasks.")
            return success_count > 0

        undo_manager.push_operation(
            description=f"Update tags for {len(undo_data)} tasks",
            undo_func=undo_func
        )

    click.echo(f"\nUpdated tags for {updated_count} tasks:")
    for change in changes_log:
        click.echo(change)

    if updated_tasks_list and not use_google_tasks:
        # Auto-save (CLI option overrides config)
        from gtasks_cli.storage.config_manager import ConfigManager
        config_manager = ConfigManager(account_name=task_manager.account_name)
        cli_auto_save = getattr(task_manager, 'cli_auto_save', None)
        
        # Use CLI option if provided, otherwise use config
        if cli_auto_save is not None:
            auto_save = cli_auto_save
        else:
            auto_save = config_manager.get('sync.auto_save', False)
        
        if auto_save:
            from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager
            click.echo("Auto-saving to Google Tasks...")
            sync_manager = AdvancedSyncManager(task_manager.storage, task_manager.google_client)
            # Use sync_multiple_tasks for efficiency
            if sync_manager.sync_multiple_tasks(updated_tasks_list, 'update'):
                 click.echo("✅ Auto-saved to Google Tasks")
            else:
                 click.echo("⚠️ Failed to auto-save to Google Tasks")
