#!/usr/bin/env python3
"""
Google Tasks CLI - Main Entry Point
"""

import click
import os
import json
from datetime import datetime
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
    """Google Tasks CLI with superpowers ⚡

    A powerful command-line interface for managing Google Tasks with advanced features
    like task dependencies, recurrence, projects, tags, and synchronization.
    
    \b
    Examples:
      # Add a simple task
      gtasks add -t "Buy groceries"
      
      # Add a task with due date and priority
      gtasks add -t "Finish report" --due "2024-12-31" --priority high
      
      # List all pending tasks
      gtasks list --status pending
      
      # Sync with Google Tasks
      gtasks sync
      
      # Search for tasks
      gtasks search "meeting"
    """
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
    """Add a new task
    
    \b
    Examples:
      # Add a simple task
      gtasks add -t "Buy groceries"
      
      # Add a task with due date and priority
      gtasks add -t "Finish report" --due "2024-12-31T17:00:00" --priority high
      
      # Add a task with project and tags
      gtasks add -t "Code review" -p "Project X" --tags "development,review"
      
      # Add a recurring task
      gtasks add -t "Daily standup" --recurring daily
      
      # Add a task with dependencies
      gtasks add -t "Deploy to production" --depends-on "task123,task456"
      
      # Add a task using Google Tasks directly
      gtasks add -t "Team meeting" -g
    """
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
    """List all tasks
    
    \b
    Examples:
      # List all tasks
      gtasks list
      
      # List only pending tasks
      gtasks list --status pending
      
      # List high priority tasks
      gtasks list --priority high
      
      # List tasks for a specific project
      gtasks list --project "Project X"
      
      # List only recurring tasks
      gtasks list --recurring
      
      # List using Google Tasks directly
      gtasks list -g
    """
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
    """Search tasks by query string
    
    \b
    Examples:
      # Search for tasks containing "meeting"
      gtasks search meeting
      
      # Search using Google Tasks directly
      gtasks search "important" -g
    """
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
    """View detailed information about a task
    
    \b
    Examples:
      # View details of a task
      gtasks view task123
      
      # View using Google Tasks directly
      gtasks view task456 -g
    """
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
    """Mark task as done
    
    \b
    Examples:
      # Mark a task as done
      gtasks done task123
      
      # Mark using Google Tasks directly
      gtasks done task456 -g
    """
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
    """Delete a task
    
    \b
    Examples:
      # Delete a task
      gtasks delete task123
      
      # Delete using Google Tasks directly
      gtasks delete task456 -g
    """
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
    """Update a task
    
    \b
    Examples:
      # Update task title
      gtasks update task123 -t "New title"
      
      # Update task due date and priority
      gtasks update task123 --due "2024-12-31" --priority high
      
      # Update task tags
      gtasks update task123 --tags "work,important"
      
      # Clear task notes
      gtasks update task123 --notes ""
      
      # Update using Google Tasks directly
      gtasks update task456 -t "New title" -g
    """
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
@click.option('--batch', '-b', is_flag=True, help='Use batch operations for faster sync')
@click.option('--dry-run', '-d', is_flag=True, help='Preview changes without actually making them')
@click.pass_context
def sync(ctx, batch, dry_run):
    """Synchronize tasks with Google Tasks
    
    This command synchronizes your local tasks with Google Tasks, ensuring that
    changes made on either side are properly reflected on both sides.
    
    \b
    Examples:
      # Standard sync
      gtasks sync
      
      # Fast batch sync (recommended for large task lists)
      gtasks sync --batch
      
      # Preview what would be deleted without actually deleting
      gtasks sync --dry-run
      
      # Preview batch sync operations
      gtasks sync --batch --dry-run
    """
    use_offline = ctx.obj.get('OFFLINE_MODE', False)
    
    if use_offline:
        logger.info("Synchronization skipped - Offline mode enabled")
        click.echo("🚫 Cannot synchronize: Offline mode is active")
        return
    
    if dry_run:
        logger.info("Dry-run mode enabled for synchronization")
        click.echo("🔍 Dry-run mode: Previewing changes without actually making them")
    
    logger.info("Synchronizing with Google Tasks")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    # Create task manager with Google Tasks enabled
    task_manager = TaskManager(use_google_tasks=True)
    
    try:
        if batch:
            # Use the new batch sync method
            if task_manager.batch_sync_with_google_tasks(dry_run=dry_run):
                if dry_run:
                    click.echo("✅ Batch synchronization preview completed successfully!")
                else:
                    click.echo("✅ Batch synchronization with Google Tasks completed successfully!")
            else:
                click.echo("❌ Failed to batch synchronize with Google Tasks!")
                exit(1)
        else:
            # Use standard sync method
            if task_manager.sync_with_google_tasks():
                if dry_run:
                    click.echo("✅ Synchronization preview completed successfully!")
                else:
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
    """Authenticate with Google Tasks API
    
    \b
    Examples:
      # Authenticate with Google Tasks
      gtasks auth
    """
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


@cli.command()
def deletion_log():
    """View the deletion log
    
    This command shows a log of all tasks that have been deleted,
    including the reason for deletion.
    
    \b
    Examples:
      # View deletion log
      gtasks deletion-log
    """
    logger.info("Viewing deletion log")
    
    import os
    deletion_log_file = os.path.join(
        os.path.expanduser("~"), ".gtasks", "deletion_log.json"
    )
    
    if not os.path.exists(deletion_log_file):
        click.echo("No deletion log found.")
        return
    
    try:
        with open(deletion_log_file, 'r') as f:
            deletion_log = json.load(f)
    except json.JSONDecodeError:
        click.echo("Error reading deletion log file.")
        return
    
    if not deletion_log:
        click.echo("Deletion log is empty.")
        return
    
    click.echo("Google Tasks Deletion Log")
    click.echo("=" * 50)
    click.echo(f"Total deletions: {len(deletion_log)}")
    click.echo()
    
    # Sort by timestamp (newest first)
    deletion_log.sort(key=lambda x: x['timestamp'], reverse=True)
    
    for entry in deletion_log:
        timestamp = entry['timestamp']
        task_title = entry['task_title']
        task_id = entry['task_id']
        reason = entry['reason']
        
        # Format the timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            formatted_time = timestamp
        
        click.echo(f"Time: {formatted_time}")
        click.echo(f"Task: {task_title}")
        click.echo(f"ID: {task_id}")
        click.echo(f"Reason: {reason}")
        click.echo("-" * 30)


@cli.command()
@click.option('--dry-run', '-d', is_flag=True, help='Preview changes without actually making them')
@click.option('--yes', is_flag=True, help='Confirm the action without prompting.')
@click.pass_context
def deduplicate(ctx, dry_run, yes):
    """Remove duplicate tasks while preserving one copy of each
    
    This command identifies and removes duplicate tasks from all task lists,
    keeping only one copy of each task.
    
    \b
    Examples:
      # Preview duplicate removal
      gtasks deduplicate --dry-run
      
      # Actually remove duplicates
      gtasks deduplicate
    """
    logger.info("Starting duplicate removal process")
    
    if not yes and not dry_run:
        if not click.confirm("Are you sure you want to remove duplicate tasks?"):
            return
    
    if dry_run:
        click.echo("🔍 Dry-run mode: Previewing duplicates without actually removing them")
    else:
        click.echo("🗑️ Removing duplicate tasks...")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
    from gtasks_cli.models.task import TaskStatus
    import hashlib
    from collections import defaultdict
    
    # Connect to Google Tasks
    google_client = GoogleTasksClient()
    if not google_client.connect():
        click.echo("❌ Failed to connect to Google Tasks")
        exit(1)
    
    click.echo("✅ Connected to Google Tasks API")
    
    # Get all task lists
    tasklists = google_client.list_tasklists()
    total_removed = 0
    total_errors = 0
    
    for tasklist in tasklists:
        tasklist_id = tasklist['id']
        tasklist_title = tasklist['title']
        
        click.echo(f"\nProcessing '{tasklist_title}' list...")
        
        # Get all tasks (including deleted) from this list
        all_tasks = google_client.list_tasks(
            tasklist_id=tasklist_id,
            show_completed=True,
            show_hidden=True,
            show_deleted=True
        )
        
        click.echo(f"  Total tasks in list: {len(all_tasks)}")
        
        # Group tasks by signature
        def create_task_signature(task):
            """Create a signature for a task based on its key attributes"""
            signature_parts = [
                str(task.title or ''),
                str(task.description or ''),
                str(task.due) if task.due else '',
                str(task.status.value) if hasattr(task.status, 'value') else str(task.status)
            ]
            
            signature_string = '|'.join(signature_parts)
            return hashlib.md5(signature_string.encode('utf-8')).hexdigest()
        
        task_groups = defaultdict(list)
        for task in all_tasks:
            signature = create_task_signature(task)
            task_groups[signature].append(task)
        
        # Find duplicates (groups with more than one task)
        duplicates = []
        for signature, tasks in task_groups.items():
            if len(tasks) > 1:
                # Sort by modification date to keep the most recent one
                tasks.sort(key=lambda t: t.modified_at or t.created_at, reverse=True)
                # Keep the first (most recent) and mark others for deletion
                duplicates.extend(tasks[1:])
        
        click.echo(f"  Found {len(duplicates)} duplicate tasks")
        
        if not duplicates:
            continue
            
        # Show sample duplicates
        if len(duplicates) <= 10:
            click.echo("  Duplicates to be removed:")
            for i, task in enumerate(duplicates):
                mod_date = task.modified_at or task.created_at
                click.echo(f"    {i+1}. {task.title} (ID: {task.id}, Modified: {mod_date})")
        else:
            click.echo("  Sample of duplicates to be removed:")
            for i, task in enumerate(duplicates[:10]):
                mod_date = task.modified_at or task.created_at
                click.echo(f"    {i+1}. {task.title} (ID: {task.id}, Modified: {mod_date})")
            click.echo(f"    ... and {len(duplicates) - 10} more")
        
        # Remove duplicates if not in dry-run mode
        if not dry_run:
            removed_count = 0
            failed_count = 0
            
            for task in duplicates:
                try:
                    # Delete the task
                    success = google_client.delete_task(task.id, tasklist_id=tasklist_id)
                    if success:
                        removed_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to remove {task.title}: {e}")
                    failed_count += 1
            
            click.echo(f"  Removed: {removed_count}, Failed: {failed_count}")
            total_removed += removed_count
            total_errors += failed_count
    
    # Summary
    if dry_run:
        click.echo(f"\n📊 Dry-run Summary:")
        click.echo(f"   Total duplicate tasks found: {total_removed + total_errors}")
    else:
        click.echo(f"\n📊 Removal Summary:")
        click.echo(f"   Successfully removed: {total_removed}")
        click.echo(f"   Failed to remove: {total_errors}")
        click.echo(f"   Total processed: {total_removed + total_errors}")
    
    if total_removed > 0 and not dry_run:
        click.echo("\n✅ Duplicate removal completed.")
        click.echo("You may want to run 'gtasks sync' to ensure consistency.")


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