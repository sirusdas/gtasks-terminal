#!/usr/bin/env python3
"""
Task list management commands for Google Tasks CLI
"""

import click
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient

# Set up logger
logger = setup_logger(__name__)


@click.group()
def tasklist():
    """Manage task lists in Google Tasks."""
    pass


@tasklist.command()
@click.option('--account', '-a', help='Account name for multi-account support')
@click.pass_context
def list(ctx, account):
    """List all task lists."""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'sqlite')
    
    # Determine the account to use
    if account:
        # Explicitly specified account
        account_name = account
    else:
        # Check context object for account
        account_name = ctx.obj.get('account_name')
    
    logger.info(f"Listing task lists {'(Google Tasks)' if use_google_tasks else '(Local)'} for account: {account_name or 'default'}")
    
    if use_google_tasks:
        # Use Google Tasks API to list task lists
        try:
            google_client = GoogleTasksClient(account_name=account_name)
            
            if not google_client.connect():
                click.echo("❌ Failed to connect to Google Tasks")
                return False
            
            # List all task lists
            task_lists = google_client.list_tasklists()
            
            total_tasks = 0
            click.echo(f"📋 Found {len(task_lists)} task list(s):")
            for i, task_list in enumerate(task_lists, 1):
                title = task_list.get('title', 'Untitled')
                task_list_id = task_list.get('id')
                # List tasks in this task list
                tasks = google_client.list_tasks(tasklist_id=task_list_id)
                task_count = len(tasks)
                total_tasks += task_count
                click.echo(f"  {i:2d}. {title} (ID: {task_list_id}) - {task_count} tasks")
            
            click.echo(f"\n📊 Total tasks across all lists: {total_tasks}")
            return True
        except Exception as e:
            logger.error(f"Error listing task lists: {e}")
            click.echo(f"❌ Error listing task lists: {e}")
            return False
    else:
        # For local mode, just list the distinct list titles from the database
        task_manager = TaskManager(
            use_google_tasks=use_google_tasks,
            storage_backend=storage_backend,
            account_name=account_name
        )
        
        # Get all tasks to extract unique list titles
        all_tasks = task_manager.list_tasks()
        
        # Group tasks by list title
        lists_with_task_counts = {}
        for task in all_tasks:
            list_title = getattr(task, 'list_title', 'Tasks')
            if list_title not in lists_with_task_counts:
                lists_with_task_counts[list_title] = 0
            lists_with_task_counts[list_title] += 1
        
        click.echo(f"📋 Found {len(lists_with_task_counts)} list(s):")
        for i, (list_title, task_count) in enumerate(lists_with_task_counts.items(), 1):
            click.echo(f"  {i:2d}. {list_title} - {task_count} tasks")
        
        click.echo(f"\n📊 Total tasks across all lists: {len(all_tasks)}")
        return True


@tasklist.command()
@click.argument('list_name')
@click.option('--account', '-a', help='Account name for multi-account support')
@click.option('--force', '-f', is_flag=True, help='Force delete without confirmation')
@click.pass_context
def delete(ctx, list_name, account, force):
    """Delete a task list and all tasks in it."""
    use_google_tasks = ctx.obj.get('use_google_tasks', False)
    storage_backend = ctx.obj.get('storage_backend', 'sqlite')
    
    # Determine the account to use
    if account:
        # Explicitly specified account
        account_name = account
    else:
        # Check context object for account
        account_name = ctx.obj.get('account_name')
    
    logger.info(f"Deleting task list '{list_name}' {'(Google Tasks)' if use_google_tasks else '(Local)'} for account: {account_name or 'default'}")
    
    if use_google_tasks:
        # Use Google Tasks API to delete the task list
        try:
            google_client = GoogleTasksClient(account_name=account_name)
            
            if not google_client.connect():
                click.echo("❌ Failed to connect to Google Tasks")
                return False
            
            # Find the task list by name
            task_lists = google_client.list_tasklists()
            target_list = None
            for task_list in task_lists:
                if task_list.get('title', '').lower() == list_name.lower():
                    target_list = task_list
                    break
            
            if not target_list:
                click.echo(f"❌ Task list '{list_name}' not found")
                return False
            
            task_list_id = target_list['id']
            title = target_list.get('title', 'Untitled')
            
            # Count tasks in this list
            tasks = google_client.list_tasks(tasklist_id=task_list_id)
            task_count = len(tasks)
            
            if not force:
                confirm = click.confirm(f"Are you sure you want to delete the list '{title}' and all {task_count} tasks in it? This cannot be undone!")
                if not confirm:
                    click.echo("❌ Deletion cancelled")
                    return False
            
            # Delete all tasks in the list first
            for task in tasks:
                google_client.delete_task(task['id'], task_list_id)
                logger.debug(f"Deleted task {task['id']} from list {task_list_id}")
            
            # Then delete the task list itself
            google_client.delete_tasklist(task_list_id)
            click.echo(f"✅ Successfully deleted task list '{title}' and {task_count} tasks")
            return True
        except Exception as e:
            logger.error(f"Error deleting task list: {e}")
            click.echo(f"❌ Error deleting task list: {e}")
            return False
    else:
        # For local mode, we need to delete all tasks associated with this list
        task_manager = TaskManager(
            use_google_tasks=use_google_tasks,
            storage_backend=storage_backend,
            account_name=account_name
        )
        
        # Get all tasks to find those in the specified list
        all_tasks = task_manager.list_tasks()
        tasks_to_delete = [task for task in all_tasks 
                          if getattr(task, 'list_title', 'Tasks').lower() == list_name.lower()]
        
        if not tasks_to_delete:
            click.echo(f"❌ Task list '{list_name}' not found")
            return False
        
        if not force:
            confirm = click.confirm(f"Are you sure you want to delete the list '{list_name}' and all {len(tasks_to_delete)} tasks in it? This cannot be undone!")
            if not confirm:
                click.echo("❌ Deletion cancelled")
                return False
        
        # Delete the tasks
        deleted_count = 0
        for task in tasks_to_delete:
            try:
                task_manager.delete_task(task.id)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete task {task.id}: {e}")
        
        click.echo(f"✅ Successfully deleted {deleted_count} tasks from list '{list_name}'")
        return True


# Make the command available
if __name__ == '__main__':
    tasklist()