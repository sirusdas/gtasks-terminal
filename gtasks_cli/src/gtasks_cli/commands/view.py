#!/usr/bin/env python3
"""
View command for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.argument('task_id')
@click.pass_context
def view(ctx, task_id):
    """View detailed information about a task"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Viewing task: {task_id} {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    # Create task manager
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    # Get the task
    task = task_manager.get_task(task_id)
    
    if not task:
        click.echo(f"❌ Task {task_id} not found!")
        exit(1)
    
    # For enum values, we need to check if they are already strings or enum instances
    status_value = task.status if isinstance(task.status, str) else task.status.value
    priority_value = task.priority if isinstance(task.priority, str) else task.priority.value
    
    status_icon = {
        'pending': '⏳',
        'in_progress': '🔄',
        'completed': '✅',
        'waiting': '⏸️',
        'deleted': '🗑️'
    }.get(status_value, '❓')
    
    priority_icon = {
        'low': '🔽',
        'medium': '🔸',
        'high': '🔺',
        'critical': '💥'
    }.get(priority_value, '🔹')
    
    # Display task details
    click.echo("📝 Task Details")
    click.echo(f"  Title: {task.title}")
    click.echo(f"  Status: {status_icon} {status_value}")
    click.echo(f"  Priority: {priority_icon} {priority_value}")
    
    if task.description:
        click.echo(f"  Description: {task.description}")
    
    if task.due:
        from datetime import datetime
        if isinstance(task.due, datetime):
            due_str = task.due.strftime('%Y-%m-%d %H:%M')
        else:
            due_str = str(task.due)
        click.echo(f"  Due Date: {due_str}")
    
    if task.project:
        click.echo(f"  Project: {task.project}")
    
    if task.tags:
        click.echo(f"  Tags: {', '.join(task.tags)}")

    from gtasks_cli.utils.space_extractor import split_notes_and_metadata, extract_spaces_from_text
    spaces = task.spaces or extract_spaces_from_text(task.notes or task.description or "")
    if spaces:
        space_strs = []
        for s_name, s_subs in spaces.items():
            if s_subs:
                space_strs.append(f"{s_name} › {', '.join(s_subs)}")
            else:
                space_strs.append(s_name)
        click.echo(f"  Spaces: {' | '.join(space_strs)}")
    
    clean_notes = ""
    raw_notes = task.notes or task.description or ""
    if raw_notes:
        clean_notes, _, _ = split_notes_and_metadata(raw_notes)
    if clean_notes:
        click.echo(f"  Notes: {clean_notes}")
        
    if task.dependencies:
        click.echo(f"  Dependencies: {', '.join(task.dependencies)}")
        
        # Show dependency status
        tasks = task_manager.list_tasks()
        task_dict = {t.id: t for t in tasks}
        dep_statuses = []
        for dep_id in task.dependencies:
            dep_task = task_dict.get(dep_id)
            if dep_task:
                dep_status = dep_task.status if isinstance(dep_task.status, str) else dep_task.status.value
                dep_statuses.append(f"{dep_id} ({dep_status})")
            else:
                dep_statuses.append(f"{dep_id} (not found)")
        click.echo(f"    Status: {', '.join(dep_statuses)}")
    
    # Show tasks that depend on this task
    dependents = task_manager.get_dependent_tasks(task_id)
    if dependents:
        dep_ids = [dep.id for dep in dependents]
        click.echo(f"  Dependent Tasks: {', '.join(dep_ids)}")
        
    if task.recurrence_rule:
        click.echo(f"  Recurrence: {task.recurrence_rule}")
        if task.is_recurring:
            click.echo(f"    Type: Recurring task template")
        if task.recurring_task_id:
            click.echo(f"    Instance of: {task.recurring_task_id}")
    
    click.echo(f"  Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if task.modified_at:
        click.echo(f"  Modified: {task.modified_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if task.completed_at:
        click.echo(f"  Completed: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")