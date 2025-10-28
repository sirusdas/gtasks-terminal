#!/usr/bin/env python3
"""
Google Tasks CLI - Main Entry Point
"""

import click
import os
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Priority

# Set up logger
logger = setup_logger(__name__)


@click.group()
@click.version_option(version='0.1.0')
@click.option('--config', type=click.Path(), help='Config file path')
@click.option('--verbose', '-v', count=True, help='Verbose output')
@click.option('--google', '-g', is_flag=True, help='Use Google Tasks API instead of local storage')
@click.pass_context
def cli(ctx, config, verbose, google):
    """Google Tasks CLI with superpowers ⚡"""
    ctx.ensure_object(dict)
    ctx.obj['CONFIG'] = config
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['USE_GOOGLE_TASKS'] = google

    # Setup logging level based on verbosity
    if verbose >= 2:
        logger.setLevel("DEBUG")
    elif verbose == 1:
        logger.setLevel("INFO")
    
    logger.debug("Starting Google Tasks CLI")
    logger.debug(f"Config file: {config}")
    logger.debug(f"Verbosity level: {verbose}")
    logger.debug(f"Use Google Tasks: {google}")


@cli.command()
@click.option('--title', '-t', required=True, help='Task title')
@click.option('--description', '-d', help='Task description')
@click.option('--due', help='Due date (ISO format, e.g., 2024-12-31 or 2024-12-31T15:30:00)')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              default='medium', help='Task priority')
@click.option('--project', '-p', help='Project name')
@click.option('--tags', '-g', help='Task tags (comma-separated)')
@click.option('--notes', '-n', help='Task notes')
@click.option('--depends-on', '-D', help='Task IDs this task depends on (comma-separated)')
@click.option('--recurring', '-r', help='Recurrence rule (e.g., daily, weekly, monthly, yearly, or "every 2 weeks")')
@click.pass_context
def add(ctx, title, description, due, priority, project, tags, notes, depends_on, recurring):
    """Add a new task"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Adding task: {title} {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    # Convert priority string to enum
    priority_enum = Priority(priority)
    
    # Parse tags if provided
    tags_list = []
    if tags:
        tags_list = [tag.strip() for tag in tags.split(',')]
    
    # Parse dependencies if provided
    dependencies_list = []
    if depends_on:
        dependencies_list = [dep.strip() for dep in depends_on.split(',')]
    
    # Create task manager and task
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    task = task_manager.create_task(
        title=title,
        description=description,
        due=due,
        priority=priority_enum,
        project=project,
        tags=tags_list,
        notes=notes,
        dependencies=dependencies_list,
        recurrence_rule=recurring
    )
    
    click.echo(f"✅ Task '{title}' (ID: {task.id}) with priority '{priority}' added successfully!")


@cli.command()
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'waiting', 'deleted']), 
              help='Filter by status')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              help='Filter by priority')
@click.option('--project', help='Filter by project')
@click.option('--recurring', '-r', is_flag=True, help='Show only recurring tasks')
@click.pass_context
def list(ctx, status, priority, project, recurring):
    """List all tasks"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Listing tasks {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    from gtasks_cli.models.task import TaskStatus
    
    # Create task manager
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    # Convert string parameters to enums where needed
    status_enum = TaskStatus(status) if status else None
    priority_enum = Priority(priority) if priority else None
    
    tasks = task_manager.list_tasks(
        status=status_enum,
        priority=priority_enum,
        project=project
    )
    
    # Filter for recurring tasks if requested
    if recurring:
        tasks = [task for task in tasks if task.is_recurring]
    
    if not tasks:
        click.echo("No tasks found.")
        return
    
    click.echo(f"📋 Found {len(tasks)} task(s):")
    for task in tasks:
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
            'critical': '🔴'
        }.get(priority_value, '🔹')
        
        # Format due date if it exists
        due_info = ""
        if task.due:
            from datetime import datetime
            if isinstance(task.due, datetime):
                due_info = f" (Due: {task.due.strftime('%Y-%m-%d %H:%M')})"
            else:
                due_info = f" (Due: {task.due})"
        
        # Format project if it exists
        project_info = ""
        if task.project:
            project_info = f" [Project: {task.project}]"
            
        # Format tags if they exist
        tags_info = ""
        if task.tags:
            tags_info = f" [Tags: {', '.join(task.tags)}]"
            
        # Format dependencies if they exist
        deps_info = ""
        if task.dependencies:
            deps_info = f" [Depends on: {', '.join(task.dependencies)}]"
            
        # Format recurrence if it exists
        recurrence_info = ""
        if task.recurrence_rule:
            recurrence_info = f" [🔁 {task.recurrence_rule}]"
        
        click.echo(f"  {status_icon} {priority_icon} {task.title} (ID: {task.id}){due_info}{project_info}{tags_info}{deps_info}{recurrence_info}")


@cli.command()
@click.argument('query')
@click.pass_context
def search(ctx, query):
    """Search tasks by query string"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    use_offline = ctx.obj.get('OFFLINE_MODE', False)
    
    if use_offline and use_google_tasks:
        logger.info("Operating in offline mode - searching local tasks only")
        use_google_tasks = False
    
    logger.info(f"Searching tasks with query: {query} {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    # Create task manager
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    # Search tasks
    tasks = task_manager.search_tasks(query)
    
    if not tasks:
        click.echo("No tasks found matching your query.")
        return
    
    click.echo(f"🔍 Found {len(tasks)} task(s) matching '{query}':")
    for task in tasks:
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
            'critical': '🔴'
        }.get(priority_value, '🔹')
        
        # Format due date if it exists
        due_info = ""
        if task.due:
            from datetime import datetime
            if isinstance(task.due, datetime):
                due_info = f" (Due: {task.due.strftime('%Y-%m-%d %H:%M')})"
            else:
                due_info = f" (Due: {task.due})"
        
        # Format project if it exists
        project_info = ""
        if task.project:
            project_info = f" [Project: {task.project}]"
            
        # Format tags if they exist
        tags_info = ""
        if task.tags:
            tags_info = f" [Tags: {', '.join(task.tags)}]"
        
        click.echo(f"  {status_icon} {priority_icon} {task.title} (ID: {task.id}){due_info}{project_info}{tags_info}")


@cli.command()
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
        'critical': '🔴'
    }.get(priority_value, '🔹')
    
    # Display task details
    click.echo(f"📝 Task Details (ID: {task.id})")
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
    
    if task.notes:
        click.echo(f"  Notes: {task.notes}")
        
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


@cli.command()
@click.argument('task_id')
@click.pass_context
def done(ctx, task_id):
    """Mark task as done"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Marking task {task_id} as done {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    if task_manager.complete_task(task_id):
        click.echo(f"✅ Task {task_id} marked as done!")
    else:
        # Check if task is blocked by dependencies
        tasks = task_manager.list_tasks()
        task_dict = {t.id: t for t in tasks}
        task = task_dict.get(task_id)
        if task and not task_manager._can_complete_task(task, tasks):
            click.echo(f"❌ Task {task_id} cannot be completed because it has unmet dependencies!")
        else:
            click.echo(f"❌ Task {task_id} not found!")
        exit(1)


@cli.command()
@click.argument('task_id')
@click.pass_context
def delete(ctx, task_id):
    """Delete a task"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Deleting task {task_id} {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    # Try to delete the task (mark as deleted)
    if task_manager.delete_task(task_id):
        click.echo(f"🗑️ Task {task_id} deleted!")
    else:
        click.echo(f"❌ Task {task_id} not found!")
        exit(1)


@cli.command()
@click.argument('task_id')
@click.option('--title', '-t', help='New task title')
@click.option('--description', '-d', help='New task description')
@click.option('--due', help='New due date (ISO format, e.g., 2024-12-31 or 2024-12-31T15:30:00)')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), 
              help='New task priority')
@click.option('--project', '-p', help='New project name')
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'waiting', 'deleted']), 
              help='New task status')
@click.option('--tags', '-g', help='New task tags (comma-separated, replaces existing tags)')
@click.option('--notes', '-n', help='New task notes')
@click.option('--depends-on', '-D', help='New task dependencies (comma-separated, replaces existing dependencies)')
@click.option('--recurring', '-r', help='New recurrence rule')
@click.pass_context
def update(ctx, task_id, title, description, due, priority, project, status, tags, notes, depends_on, recurring):
    """Update a task"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    logger.info(f"Updating task {task_id} {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    from gtasks_cli.models.task import TaskStatus, Priority
    
    task_manager = TaskManager(use_google_tasks=use_google_tasks)
    
    # Prepare update data
    update_data = {}
    if title:
        update_data['title'] = title
    if description:
        update_data['description'] = description
    if due:
        update_data['due'] = due
    if priority:
        update_data['priority'] = Priority(priority)
    if project:
        update_data['project'] = project
    if status:
        update_data['status'] = TaskStatus(status)
    if tags:
        update_data['tags'] = [tag.strip() for tag in tags.split(',')]
    if notes is not None:  # Allow empty notes to clear the field
        update_data['notes'] = notes
    if depends_on is not None:  # Allow empty dependencies to clear the field
        update_data['dependencies'] = [dep.strip() for dep in depends_on.split(',')]
    if recurring is not None:  # Allow empty recurrence to clear the field
        update_data['recurrence_rule'] = recurring
        update_data['is_recurring'] = bool(recurring)
    
    # Try to update the task
    updated_task = task_manager.update_task(task_id, **update_data)
    
    if updated_task:
        click.echo(f"✅ Task {task_id} updated successfully!")
    else:
        click.echo(f"❌ Task {task_id} not found!")
        exit(1)


@cli.command()
@click.pass_context
def sync(ctx):
    """Synchronize tasks with Google Tasks"""
    use_offline = ctx.obj.get('OFFLINE_MODE', False)
    
    if use_offline:
        logger.info("Synchronization skipped - Offline mode enabled")
        click.echo("🚫 Cannot synchronize: Offline mode is active")
        return
    
    logger.info("Synchronizing with Google Tasks")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    # Create task manager with Google Tasks enabled
    task_manager = TaskManager(use_google_tasks=True)
    
    try:
        if task_manager.sync_with_google_tasks():
            click.echo("✅ Synchronization with Google Tasks completed successfully!")
        else:
            click.echo("❌ Failed to synchronize with Google Tasks!")
            exit(1)
    except Exception as e:
        logger.error(f"Synchronization error: {e}")
        click.echo(f"❌ Synchronization error: {str(e)}")
        exit(1)


@cli.command()
def auth():
    """Authenticate with Google Tasks API"""
    logger.info("Starting Google authentication flow")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.integrations.google_auth import GoogleAuthManager
    
    # Create auth manager
    auth_manager = GoogleAuthManager()
    
    if auth_manager.authenticate():
        click.echo("✅ Successfully authenticated with Google Tasks API!")
    else:
        click.echo("❌ Failed to authenticate with Google Tasks API!")
        exit(1)


def main():
    """Main entry point for the application"""
    try:
        cli()
    except Exception as e:
        logger.error(f"Application error: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        exit(1)


if __name__ == '__main__':
    main()