#!/usr/bin/env python3
"""
Bulk update commands functionality for interactive mode
"""

import click
import re
from datetime import datetime
from typing import List, Tuple, Optional
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_bulk_update_command(task_state, task_manager, command_parts, use_google_tasks=False):
    """Handle the bulk update status command in interactive mode
    
    Command format:
    update-status C[1,2,3], DT[1,2,3], DEL[4], P[5,6], DUE[7,8,9|21-09|10:10 PM]
    
    C = Completed
    DT = Due today, DT can also have [1,2,3|09:00 PM]
    DEL = Delete
    P = Pending
    DUE = Due on with task ids|due date|due time
    """
    
    if len(command_parts) < 2:
        click.echo("Usage: update-status C[1,2,3], DT[1,2,3], DEL[4], P[5,6], DUE[7,8,9|21-09|10:10 PM]")
        click.echo("Where:")
        click.echo("  C = Completed")
        click.echo("  DT = Due today (can also specify time: DT[1,2,3|09:00 PM])")
        click.echo("  DEL = Delete")
        click.echo("  P = Pending")
        click.echo("  DUE = Due on (DUE[task_ids|date|time])")
        return

    # Join all parts after 'update-status' to form the command string
    command_string = " ".join(command_parts[1:])
    logger.debug(f"Command string: {command_string}")
    
    # Parse and process the command
    try:
        updates = _parse_bulk_update_command(command_string)
        _execute_bulk_updates(task_state, task_manager, updates, use_google_tasks)
    except Exception as e:
        logger.error(f"Error processing bulk update command: {e}", exc_info=True)
        click.echo(f"Error processing bulk update command: {e}")


def _parse_bulk_update_command(command_string: str) -> List[Tuple[str, dict]]:
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
        while i < len(command_string) and command_string[i].isupper():
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
    updated_count = 0
    error_count = 0
    
    for op_type, op_data in operations:
        try:
            if op_type == "completed":
                count = _set_tasks_status(task_state, task_manager, op_data["task_numbers"], TaskStatus.COMPLETED, use_google_tasks)
                updated_count += count
                click.echo(f"Marked {count} task(s) as completed")
                
            elif op_type == "due_today":
                count = _set_tasks_due_today(task_state, task_manager, op_data["task_numbers"], op_data["time"], use_google_tasks)
                updated_count += count
                click.echo(f"Set due date to today for {count} task(s)")
                
            elif op_type == "delete":
                count = _set_tasks_status(task_state, task_manager, op_data["task_numbers"], TaskStatus.DELETED, use_google_tasks)
                updated_count += count
                click.echo(f"Marked {count} task(s) as deleted")
                
            elif op_type == "pending":
                count = _set_tasks_status(task_state, task_manager, op_data["task_numbers"], TaskStatus.PENDING, use_google_tasks)
                updated_count += count
                click.echo(f"Marked {count} task(s) as pending")
                
            elif op_type == "due_on":
                count = _set_tasks_due_on(task_state, task_manager, op_data["task_numbers"], 
                                         op_data["date"], op_data["time"], use_google_tasks)
                updated_count += count
                click.echo(f"Set due date for {count} task(s)")
                
        except Exception as e:
            error_count += 1
            click.echo(f"Error executing {op_type} operation: {e}")
    
    click.echo(f"Bulk update completed: {updated_count} tasks updated, {error_count} errors")


def _set_tasks_status(task_state, task_manager, task_numbers: List[int], status: TaskStatus, use_google_tasks: bool) -> int:
    """Set the status of multiple tasks"""
    count = 0
    for task_num in task_numbers:
        task = task_state.get_task_by_number(task_num)
        if task:
            # For completed status, also set completed_at
            extra_params = {}
            if status == TaskStatus.COMPLETED:
                extra_params['completed_at'] = datetime.now()
                
            success = task_manager.update_task(task.id, status=status, **extra_params)
            if success:
                count += 1
                # Update the task in the task state
                _update_task_in_state(task_state, task.id, task_manager)
            else:
                click.echo(f"Failed to update task {task_num}")
        else:
            click.echo(f"Task {task_num} not found")
    return count


def _set_tasks_due_today(task_state, task_manager, task_numbers: List[int], time_str: Optional[str], use_google_tasks: bool) -> int:
    """Set tasks due date to today"""
    count = 0
    today = datetime.now().date()
    
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
                count += 1
                _update_task_in_state(task_state, task.id, task_manager)
            else:
                click.echo(f"Failed to update due date for task {task_num}")
        else:
            click.echo(f"Task {task_num} not found")
    return count


def _set_tasks_due_on(task_state, task_manager, task_numbers: List[int], date_str: str, time_str: str, use_google_tasks: bool) -> int:
    """Set tasks due on a specific date"""
    count = 0
    
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
        return 0
    
    for task_num in task_numbers:
        task = task_state.get_task_by_number(task_num)
        if task:
            success = task_manager.update_task(task.id, due=due_datetime)
            if success:
                count += 1
                _update_task_in_state(task_state, task.id, task_manager)
            else:
                click.echo(f"Failed to update due date for task {task_num}")
        else:
            click.echo(f"Task {task_num} not found")
    return count


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