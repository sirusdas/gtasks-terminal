#!/usr/bin/env python3
"""
Bulk update commands functionality for interactive mode
"""

import click
import re
from datetime import datetime, date
from typing import List, Tuple, Optional
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_bulk_update_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """Handle the bulk update status command in interactive mode
    
    Command format:
    update-status C[1,2,3], DT[1,2,3], DEL[4], P[5,6], DUE[7,8,9|21-09|10:10 PM]
    update-status ALL[C], ALL[DUE:TODAY], ALL[DUE:26-11]
    
    C = Completed
    DT = Due today, DT can also have [1,2,3|09:00 PM]
    DEL = Delete
    P = Pending
    DUE = Due on with task ids|due date|due time
    ALL = Apply operation to all currently displayed tasks
    """
    
    if len(command_parts) < 2:
        click.echo("Usage: update-status C[1,2,3], DT[1,2,3], DEL[4], P[5,6], DUE[7,8,9|21-09|10:10 PM]")
        click.echo("       update-status ALL[C], ALL[DUE:TODAY], ALL[DUE:26-11]")
        click.echo("Where:")
        click.echo("  C = Completed")
        click.echo("  DT = Due today (can also specify time: DT[1,2,3|09:00 PM])")
        click.echo("  DEL = Delete")
        click.echo("  P = Pending")
        click.echo("  DUE = Due on (DUE[task_ids|date|time])")
        click.echo("  ALL = Apply to all currently displayed tasks")
        return

    # Join all parts after 'update-status' to form the command string
    command_string = " ".join(command_parts[1:])
    logger.debug(f"Command string: {command_string}")
    
    # Parse and process the command
    try:
        updates = _parse_bulk_update_command(command_string, task_state)
        _execute_bulk_updates(task_state, task_manager, updates, use_google_tasks)
    except Exception as e:
        logger.error(f"Error processing bulk update command: {e}", exc_info=True)
        click.echo(f"Error processing bulk update command: {e}")


def _parse_bulk_update_command(command_string: str, task_state=None) -> List[Tuple[str, dict]]:
    """Parse the bulk update command string into a list of operations
    
    Returns:
        List of tuples (operation_type, operation_data)
    """
    operations = []
    
    # Parse operations manually to handle commas inside brackets correctly
    i = 0
    while i < len(command_string):
        # Skip whitespace
        while i < len(command_string) and command_string[i].isspace():
            i += 1
            
        if i >= len(command_string):
            break
            
        # Find operation type (uppercase letters)
        start = i
        while i < len(command_string) and command_string[i].isalpha() and command_string[i].isupper():
            i += 1
            
        if i == start:
            raise ValueError(f"Invalid syntax: Expected operation type at position {i}")
            
        op_type = command_string[start:i]
        logger.debug(f"Found operation type: {op_type}")
        
        # Expect opening bracket
        if i >= len(command_string) or command_string[i] != '[':
            raise ValueError(f"Invalid syntax: Expected '[' after {op_type}")
        i += 1
        
        # Find closing bracket and extract content
        start = i
        bracket_count = 1
        while i < len(command_string) and bracket_count > 0:
            if command_string[i] == '[':
                bracket_count += 1
            elif command_string[i] == ']':
                bracket_count -= 1
            if bracket_count > 0:  # Don't include the closing bracket
                i += 1
                
        if bracket_count > 0:
            raise ValueError(f"Invalid syntax: Unmatched '[' in {op_type} operation")
            
        op_data = command_string[start:i]
        logger.debug(f"Parsed operation: type={op_type}, data={op_data}")
        i += 1  # Skip closing bracket
        
        if op_type == "C":  # Completed
            task_numbers = _parse_task_numbers(op_data)
            operations.append(("completed", {"task_numbers": task_numbers}))
            
        elif op_type == "DT":  # Due today
            # Check if time is specified: DT[1,2,3|09:00 PM]
            if '|' in op_data:
                task_part, time_part = op_data.split('|', 1)
                task_numbers = _parse_task_numbers(task_part)
                operations.append(("due_today", {"task_numbers": task_numbers, "time": time_part.strip()}))
            else:
                task_numbers = _parse_task_numbers(op_data)
                operations.append(("due_today", {"task_numbers": task_numbers, "time": None}))
                
        elif op_type == "DEL":  # Delete
            task_numbers = _parse_task_numbers(op_data)
            operations.append(("delete", {"task_numbers": task_numbers}))
            
        elif op_type == "P":  # Pending
            task_numbers = _parse_task_numbers(op_data)
            operations.append(("pending", {"task_numbers": task_numbers}))
            
        elif op_type == "DUE":  # Due on specific date
            # Format: DUE[task_ids|date|time]
            if '|' not in op_data:
                raise ValueError(f"DUE operation requires format: DUE[task_ids|date|time]")
                
            parts = op_data.split('|')
            if len(parts) < 3:
                raise ValueError(f"DUE operation requires format: DUE[task_ids|date|time]")
                
            task_part, date_part, time_part = parts[0], parts[1], parts[2]
            task_numbers = _parse_task_numbers(task_part)
            operations.append(("due_on", {
                "task_numbers": task_numbers,
                "date": date_part.strip(),
                "time": time_part.strip()
            }))
            
        elif op_type == "ALL":  # Apply operation to all displayed tasks
            # Parse the operation inside ALL[]
            # e.g., ALL[C], ALL[DUE:TODAY], ALL[DUE:26-11]
            op_data = op_data.strip()
            
            # Get all task numbers from current display
            all_task_numbers = list(range(1, len(task_state.tasks) + 1)) if task_state else []
            
            if not all_task_numbers:
                raise ValueError("No tasks currently displayed")
                
            if op_data.upper() == "C":
                operations.append(("completed", {"task_numbers": all_task_numbers}))
            elif op_data.upper() == "P":
                operations.append(("pending", {"task_numbers": all_task_numbers}))
            elif op_data.upper() == "DEL":
                operations.append(("delete", {"task_numbers": all_task_numbers}))
            elif op_data.upper().startswith("DUE:"):
                # Handle due date operations
                due_spec = op_data[4:]  # Remove "DUE:" prefix
                if due_spec.upper() == "TODAY":
                    operations.append(("due_today", {"task_numbers": all_task_numbers, "time": None}))
                elif "-" in due_spec:
                    # Format: DD-MM
                    try:
                        day, month = map(int, due_spec.split('-'))
                        operations.append(("due_on_all", {
                            "task_numbers": all_task_numbers,
                            "date": f"{day:02d}-{month:02d}",
                            "time": "11:59 PM"  # End of day by default
                        }))
                    except ValueError:
                        raise ValueError(f"Invalid date format in ALL[DUE:{due_spec}]. Use DD-MM format.")
                else:
                    raise ValueError(f"Invalid DUE specification in ALL[{op_data}]. Use TODAY or DD-MM format.")
            elif op_data.upper() == "DT":
                operations.append(("due_today", {"task_numbers": all_task_numbers, "time": None}))
            elif "|" in op_data:
                # Handle DT with optional time like DT|09:00 PM
                parts = op_data.split("|", 1)
                if parts[0].upper() == "DT":
                    operations.append(("due_today", {"task_numbers": all_task_numbers, "time": parts[1].strip()}))
                else:
                    raise ValueError(f"Invalid DT specification in ALL[{op_data}]. Use DT or DT|time.")
            else:
                raise ValueError(f"Unsupported operation in ALL[{op_data}]. Supported: C, P, DEL, DT, DUE:TODAY, DUE:DD-MM")
            
        else:
            raise ValueError(f"Unknown operation type: {op_type}")
        
        # Skip comma and whitespace
        while i < len(command_string) and (command_string[i] == ',' or command_string[i].isspace()):
            i += 1
            
    logger.debug(f"Final operations: {operations}")
    return operations


def _parse_task_numbers(task_string: str) -> List[int]:
    """Parse a string of task numbers like '1,2,3' into a list of integers"""
    if not task_string:
        return []
        
    try:
        result = [int(x.strip()) for x in task_string.split(',') if x.strip()]
        return result
    except ValueError:
        raise ValueError(f"Invalid task number in: {task_string}")


def _execute_bulk_updates(task_state, task_manager, operations: List[Tuple[str, dict]], use_google_tasks: bool):
    """Execute the parsed bulk update operations"""
    updated_tasks = []
    error_count = 0
    
    # Check if any operation uses ALL - if so, ask for confirmation
    has_all_operation = any(len(op_data.get("task_numbers", [])) == len(task_state.tasks) 
                           for _, op_data in operations)
    
    if has_all_operation:
        # Count total tasks that would be affected
        total_affected = sum(len(op_data["task_numbers"]) for _, op_data in operations)
        if not click.confirm(f"You are about to update {total_affected} tasks. Do you want to continue?"):
            click.echo("Operation cancelled.")
            return
    
    for op_type, op_data in operations:
        try:
            if op_type == "completed":
                tasks = _set_tasks_status(task_state, task_manager, op_data["task_numbers"], TaskStatus.COMPLETED, use_google_tasks)
                updated_tasks.extend(tasks)
                click.echo(f"Marked {len(tasks)} task(s) as completed")
                
            elif op_type == "due_today":
                tasks = _set_tasks_due_today(task_state, task_manager, op_data["task_numbers"], op_data["time"], use_google_tasks)
                updated_tasks.extend(tasks)
                click.echo(f"Set due date to today for {len(tasks)} task(s)")
                
            elif op_type == "delete":
                tasks = _set_tasks_status(task_state, task_manager, op_data["task_numbers"], TaskStatus.DELETED, use_google_tasks)
                updated_tasks.extend(tasks)
                click.echo(f"Marked {len(tasks)} task(s) as deleted")
                
            elif op_type == "pending":
                tasks = _set_tasks_status(task_state, task_manager, op_data["task_numbers"], TaskStatus.PENDING, use_google_tasks)
                updated_tasks.extend(tasks)
                click.echo(f"Marked {len(tasks)} task(s) as pending")
                
            elif op_type == "due_on":
                tasks = _set_tasks_due_on(task_state, task_manager, op_data["task_numbers"], 
                                         op_data["date"], op_data["time"], use_google_tasks)
                updated_tasks.extend(tasks)
                click.echo(f"Set due date for {len(tasks)} task(s)")
                
            elif op_type == "due_on_all":
                tasks = _set_tasks_due_on(task_state, task_manager, op_data["task_numbers"], 
                                         op_data["date"], op_data["time"], use_google_tasks)
                updated_tasks.extend(tasks)
                click.echo(f"Set due date for {len(tasks)} task(s)")
                
        except Exception as e:
            error_count += 1
            click.echo(f"Error executing {op_type} operation: {e}")
    
    click.echo(f"Bulk update completed: {len(updated_tasks)} tasks updated, {error_count} errors")

    if updated_tasks and not use_google_tasks:
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
            if sync_manager.sync_multiple_tasks(updated_tasks, 'update'):
                 click.echo("✅ Auto-saved to Google Tasks")
            else:
                 click.echo("⚠️ Failed to auto-save to Google Tasks")


def _set_tasks_status(task_state, task_manager, task_numbers: List[int], status: TaskStatus, use_google_tasks: bool) -> List[Task]:
    """Set the status of multiple tasks"""
    updated_tasks = []
    for task_num in task_numbers:
        task = task_state.get_task_by_number(task_num)
        if task:
            # For completed status, also set completed_at
            extra_params = {}
            if status == TaskStatus.COMPLETED:
                extra_params['completed_at'] = datetime.now()
                
            success = task_manager.update_task(task.id, status=status, **extra_params)
            if success:
                # Get the updated task
                updated_task = task_manager.get_task(task.id)
                if updated_task:
                    updated_tasks.append(updated_task)
                # Update the task in the task state
                _update_task_in_state(task_state, task.id, task_manager)
            else:
                click.echo(f"Failed to update task {task_num}")
        else:
            click.echo(f"Task {task_num} not found")
    return updated_tasks


def _set_tasks_due_today(task_state, task_manager, task_numbers: List[int], time_str: Optional[str], use_google_tasks: bool) -> List[Task]:
    """Set tasks due date to today"""
    updated_tasks = []
    today = date.today()
    
    # Parse time if provided
    due_datetime = None
    if time_str:
        try:
            # Parse time like "09:00 PM" or "15:30"
            if "AM" in time_str.upper() or "PM" in time_str.upper():
                time_obj = datetime.strptime(time_str, "%I:%M %p").time()
            else:
                time_obj = datetime.strptime(time_str, "%H:%M").time()
            due_datetime = datetime.combine(today, time_obj)
        except ValueError:
            click.echo(f"Invalid time format: {time_str}. Using end of day.")
            due_datetime = datetime.combine(today, datetime.max.time())
    else:
        # End of day
        due_datetime = datetime.combine(today, datetime.max.time())
    
    for task_num in task_numbers:
        task = task_state.get_task_by_number(task_num)
        if task:
            success = task_manager.update_task(task.id, due=due_datetime)
            if success:
                # Get the updated task
                updated_task = task_manager.get_task(task.id)
                if updated_task:
                    updated_tasks.append(updated_task)
                _update_task_in_state(task_state, task.id, task_manager)
            else:
                click.echo(f"Failed to update due date for task {task_num}")
        else:
            click.echo(f"Task {task_num} not found")
    return updated_tasks


def _set_tasks_due_on(task_state, task_manager, task_numbers: List[int], date_str: str, time_str: str, use_google_tasks: bool) -> List[Task]:
    """Set tasks due on a specific date"""
    updated_tasks = []
    
    try:
        # Parse date like "21-09" (assuming current year)
        day, month = map(int, date_str.split('-'))
        year = datetime.now().year
        due_date = datetime(year, month, day)
        
        # Parse time like "10:10 PM" or "15:30"
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
        else:
            time_obj = datetime.strptime(time_str, "%H:%M").time()
        due_datetime = datetime.combine(due_date.date(), time_obj)
    except ValueError as e:
        click.echo(f"Invalid date/time format: {date_str} {time_str} - {e}")
        return []
    
    for task_num in task_numbers:
        task = task_state.get_task_by_number(task_num)
        if task:
            success = task_manager.update_task(task.id, due=due_datetime)
            if success:
                # Get the updated task
                updated_task = task_manager.get_task(task.id)
                if updated_task:
                    updated_tasks.append(updated_task)
                _update_task_in_state(task_state, task.id, task_manager)
            else:
                click.echo(f"Failed to update due date for task {task_num}")
        else:
            click.echo(f"Task {task_num} not found")
    return updated_tasks


def _update_task_in_state(task_state, task_id: str, task_manager):
    """Update a task in the task state after it's been modified"""
    # Get the updated task
    updated_task = None
    all_tasks = task_manager.list_tasks()
    for t in all_tasks:
        if t.id == task_id:
            updated_task = t
            break
    
    if updated_task:
        # Update the task in the task list
        for i, task in enumerate(task_state.tasks):
            if task.id == task_id:
                task_state.tasks[i] = updated_task
                break
        
        # Refresh the mappings
        task_state.task_number_to_id = {}
        task_state.task_id_to_number = {}
        for i, task in enumerate(task_state.tasks, 1):
            task_state.task_number_to_id[i] = task.id
            task_state.task_id_to_number[task.id] = i