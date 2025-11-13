#!/usr/bin/env python3
"""
Summary command for Google Tasks CLI
"""

import click
from datetime import datetime
from gtasks_cli.utils.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


@click.command()
@click.option('--list-id', help='Specific task list ID to summarize (default: all lists)')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed task counts')
@click.pass_context
def summary(ctx, list_id, detailed):
    """Generate a summary of tasks across all lists or a specific list"""
    use_google_tasks = ctx.obj.get('USE_GOOGLE_TASKS', False)
    storage_backend = ctx.obj.get('storage_backend', 'json')
    logger.info(f"Generating task summary {'(Google Tasks)' if use_google_tasks else '(Local)'}")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.core.task_manager import TaskManager
    
    # Create task manager
    task_manager = TaskManager(
        use_google_tasks=use_google_tasks,
        storage_backend=storage_backend
    )
    
    if use_google_tasks:
        # For Google Tasks, we need to use the Google client directly to get task lists
        from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
        google_client = GoogleTasksClient()
        if not google_client.connect():
            click.echo("❌ Failed to connect to Google Tasks API!")
            exit(1)
        
        if list_id:
            # Get specific task list
            try:
                tasklist = google_client.service.tasklists().get(tasklist=list_id).execute()
                task_lists = [tasklist]
            except Exception as e:
                click.echo(f"❌ Task list with ID {list_id} not found!")
                exit(1)
        else:
            # Get all task lists
            task_lists_result = google_client.service.tasklists().list().execute()
            task_lists = task_lists_result.get('items', [])
    else:
        # For local storage, we simulate with a single default list
        if list_id and list_id != "default":
            click.echo(f"❌ Task list with ID {list_id} not found!")
            exit(1)
        task_lists = [{"id": "default", "title": "Default Local List"}]
    
    if not task_lists:
        click.echo("❌ No task lists found!")
        exit(1)
    
    # Summary counters
    total_tasks_all_lists = 0
    total_completed_all_lists = 0
    total_pending_all_lists = 0
    total_in_progress_all_lists = 0
    total_waiting_all_lists = 0
    total_deleted_all_lists = 0
    
    # Process each task list
    for tasklist in task_lists:
        tasklist_id = tasklist['id']
        tasklist_title = tasklist['title']
        
        click.echo(f"\n{'='*50}")
        click.echo(f"📋 Task List: '{tasklist_title}' (ID: {tasklist_id})")
        click.echo(f"{'='*50}")
        
        # Get all tasks from this list
        if use_google_tasks:
            from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
            google_client = GoogleTasksClient()
            if google_client.connect():
                # Get all tasks with all statuses
                all_tasks = google_client.list_tasks(
                    tasklist_id=tasklist_id,
                    show_completed=True,
                    show_hidden=True,
                    show_deleted=True
                )
                
                # Also get just pending tasks to compare counts
                pending_tasks_only = google_client.list_tasks(
                    tasklist_id=tasklist_id,
                    show_completed=False,
                    show_hidden=False,
                    show_deleted=False
                )
                
                if detailed:
                    click.echo(f"🔍 Detailed task retrieval:")
                    click.echo(f"   All tasks (including completed/deleted): {len(all_tasks)}")
                    click.echo(f"   Pending tasks only: {len(pending_tasks_only)}")
            else:
                click.echo("❌ Failed to connect to Google Tasks API!")
                exit(1)
        else:
            all_tasks = task_manager.list_tasks()
            pending_tasks_only = [task for task in all_tasks if (
                task.status == 'pending' or 
                (hasattr(task.status, 'value') and task.status.value == 'pending')
            )]
        
        # Count tasks by status
        status_counts = {}
        total_tasks = len(all_tasks)
        
        for task in all_tasks:
            # Convert status to string if it's an enum
            status_value = task.status if isinstance(task.status, str) else task.status.value
            status_counts[status_value] = status_counts.get(status_value, 0) + 1
        
        # Display summary for this list
        completed_count = status_counts.get('completed', 0)
        pending_count = status_counts.get('pending', 0)
        in_progress_count = status_counts.get('in_progress', 0)
        waiting_count = status_counts.get('waiting', 0)
        deleted_count = status_counts.get('deleted', 0)
        
        click.echo(f"📊 Summary:")
        click.echo(f"   Total tasks: {total_tasks}")
        click.echo(f"   ✅ Completed: {completed_count}")
        click.echo(f"   ⏳ Pending: {pending_count}")
        click.echo(f"   🔄 In Progress: {in_progress_count}")
        click.echo(f"   ⏸️  Waiting: {waiting_count}")
        click.echo(f"   🗑️  Deleted: {deleted_count}")
        
        if detailed and use_google_tasks:
            click.echo(f"   ⚠️  API returned pending tasks: {len(pending_tasks_only)}")
        
        # Update overall counters
        total_tasks_all_lists += total_tasks
        total_completed_all_lists += completed_count
        total_pending_all_lists += pending_count
        total_in_progress_all_lists += in_progress_count
        total_waiting_all_lists += waiting_count
        total_deleted_all_lists += deleted_count
        
        # Show sample pending tasks (up to 10 if detailed, otherwise 5)
        max_pending = 10 if detailed else 5
        pending_tasks = [task for task in all_tasks if (
            task.status == 'pending' or 
            (hasattr(task.status, 'value') and task.status.value == 'pending')
        )]
        
        if pending_tasks:
            click.echo(f"\n📝 Sample of pending tasks (showing up to {max_pending}):")
            for i, task in enumerate(pending_tasks[:max_pending]):
                due_info = ""
                if task.due:
                    try:
                        due_info = f" (📅 {task.due.strftime('%Y-%m-%d')})"
                    except:
                        due_info = f" (📅 {task.due})"
                click.echo(f"   {i+1}. {task.title}{due_info}")
            if len(pending_tasks) > max_pending:
                click.echo(f"   ... and {len(pending_tasks) - max_pending} more")
        
        # Tasks with due dates analysis
        tasks_with_due = [task for task in all_tasks if task.due]
        if tasks_with_due:
            # Sort by due date
            tasks_with_due.sort(key=lambda x: x.due if isinstance(x.due, datetime) else str(x.due))
            
            # Overdue tasks
            now = datetime.now().astimezone()
            overdue_tasks = []
            upcoming_tasks = []
            
            for task in tasks_with_due:
                if isinstance(task.due, datetime):
                    if task.due < now:
                        overdue_tasks.append(task)
                    else:
                        # Check if due in next 7 days
                        from datetime import timedelta
                        week_from_now = now + timedelta(days=7)
                        if task.due <= week_from_now:
                            upcoming_tasks.append(task)
            
            click.echo(f"\n📅 Due Date Analysis:")
            click.echo(f"   Tasks with due dates: {len(tasks_with_due)}")
            click.echo(f"   Overdue tasks: {len(overdue_tasks)}")
            click.echo(f"   Due in next 7 days: {len(upcoming_tasks)}")
    
    # Overall summary
    if len(task_lists) > 1:
        click.echo(f"\n{'='*50}")
        click.echo(f"📈 OVERALL SUMMARY")
        click.echo(f"{'='*50}")
        click.echo(f"   Total task lists: {len(task_lists)}")
        click.echo(f"   Total tasks: {total_tasks_all_lists}")
        click.echo(f"   ✅ Completed: {total_completed_all_lists}")
        click.echo(f"   ⏳ Pending: {total_pending_all_lists}")
        click.echo(f"   🔄 In Progress: {total_in_progress_all_lists}")
        click.echo(f"   ⏸️  Waiting: {total_waiting_all_lists}")
        click.echo(f"   🗑️  Deleted: {total_deleted_all_lists}")
        if total_tasks_all_lists > 0:
            completion_rate = total_completed_all_lists / total_tasks_all_lists * 100
            click.echo(f"   Completion rate: {completion_rate:.1f}%")



