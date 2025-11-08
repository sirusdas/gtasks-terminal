#!/usr/bin/env python3
"""
Deduplicate command for Google Tasks CLI
"""

import click
import hashlib
from collections import defaultdict
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import TaskStatus

# Set up logger
logger = setup_logger(__name__)


@click.command()
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
            logger.info("User cancelled duplicate removal process")
            return
    
    if dry_run:
        click.echo("🔍 Dry-run mode: Previewing duplicates without actually removing them")
        logger.info("Running in dry-run mode")
    else:
        click.echo("🗑️ Removing duplicate tasks...")
        logger.info("Running in actual removal mode")
    
    # Import here to avoid issues with module loading
    from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
    
    # Connect to Google Tasks
    logger.info("Initializing Google Tasks client")
    google_client = GoogleTasksClient()
    if not google_client.connect():
        click.echo("❌ Failed to connect to Google Tasks")
        logger.error("Failed to connect to Google Tasks")
        exit(1)
    
    click.echo("✅ Connected to Google Tasks API")
    logger.info("Successfully connected to Google Tasks API")
    
    # Get all task lists
    logger.info("Retrieving task lists")
    tasklists = google_client.list_tasklists()
    logger.info(f"Found {len(tasklists)} task lists")
    total_removed = 0
    total_errors = 0
    
    for tasklist in tasklists:
        tasklist_id = tasklist['id']
        tasklist_title = tasklist['title']
        
        click.echo(f"\nProcessing '{tasklist_title}' list...")
        logger.info(f"Processing task list: {tasklist_title} ({tasklist_id})")
        
        # Get all tasks (including deleted) from this list
        logger.info("Retrieving tasks from list")
        all_tasks = google_client.list_tasks(
            tasklist_id=tasklist_id,
            show_completed=True,
            show_hidden=True,
            show_deleted=True
        )
        
        click.echo(f"  Total tasks in list: {len(all_tasks)}")
        logger.info(f"Retrieved {len(all_tasks)} tasks from list")
        
        # Group tasks by signature
        def create_task_signature(task):
            """Create a signature for a task based on its key attributes"""
            logger.debug(f"Creating signature for task: {task.title}")
            signature_parts = [
                str(task.title or ''),
                str(task.description or ''),
                str(task.due) if task.due else '',
                str(task.status.value) if hasattr(task.status, 'value') else str(task.status)
            ]
            
            signature_string = '|'.join(signature_parts)
            signature_hash = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
            logger.debug(f"Task signature: {signature_hash} for task: {task.title}")
            return signature_hash
        
        task_groups = defaultdict(list)
        for task in all_tasks:
            signature = create_task_signature(task)
            task_groups[signature].append(task)
        
        logger.info(f"Grouped tasks into {len(task_groups)} signature groups")
        
        # Find duplicates (groups with more than one task)
        duplicates = []
        duplicate_groups = 0
        for signature, tasks in task_groups.items():
            if len(tasks) > 1:
                logger.info(f"Found duplicate group with {len(tasks)} tasks")
                duplicate_groups += 1
                # Sort by modification date to keep the most recent one
                tasks.sort(key=lambda t: t.modified_at or t.created_at, reverse=True)
                # Keep the first (most recent) and mark others for deletion
                duplicates.extend(tasks[1:])
        
        click.echo(f"  Found {len(duplicates)} duplicate tasks in {duplicate_groups} groups")
        logger.info(f"Found {len(duplicates)} duplicate tasks in {duplicate_groups} groups")
        
        if not duplicates:
            logger.info("No duplicates found in this list")
            continue
            
        # Show sample duplicates
        if len(duplicates) <= 10:
            click.echo("  Duplicates to be removed:")
            for i, task in enumerate(duplicates):
                mod_date = task.modified_at or task.created_at
                click.echo(f"    {i+1}. {task.title} (ID: {task.id}, Modified: {mod_date})")
                logger.debug(f"Duplicate task: {task.title} (ID: {task.id})")
        else:
            click.echo("  Sample of duplicates to be removed:")
            for i, task in enumerate(duplicates[:10]):
                mod_date = task.modified_at or task.created_at
                click.echo(f"    {i+1}. {task.title} (ID: {task.id}, Modified: {mod_date})")
                logger.debug(f"Duplicate task: {task.title} (ID: {task.id})")
            click.echo(f"    ... and {len(duplicates) - 10} more")
        
        # Remove duplicates if not in dry-run mode
        if not dry_run:
            logger.info(f"Removing {len(duplicates)} duplicate tasks")
            removed_count = 0
            failed_count = 0
            
            for task in duplicates:
                try:
                    logger.info(f"Deleting task: {task.title} (ID: {task.id})")
                    # Delete the task
                    success = google_client.delete_task(task.id, tasklist_id=tasklist_id)
                    if success:
                        logger.info(f"Successfully deleted task: {task.title}")
                        removed_count += 1
                    else:
                        logger.warning(f"Failed to delete task: {task.title}")
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to remove {task.title}: {e}")
                    failed_count += 1
            
            click.echo(f"  Removed: {removed_count}, Failed: {failed_count}")
            logger.info(f"Removal results - Removed: {removed_count}, Failed: {failed_count}")
            total_removed += removed_count
            total_errors += failed_count
        else:
            # In dry-run mode, count the duplicates that would be removed
            total_removed += len(duplicates)
            logger.info("Dry-run mode: Would remove duplicates")
    
    # Summary
    if dry_run:
        click.echo(f"\n📊 Dry-run Summary:")
        click.echo(f"   Total duplicate tasks found: {total_removed + total_errors}")
        logger.info(f"Dry-run summary - Total duplicate tasks found: {total_removed + total_errors}")
    else:
        click.echo(f"\n📊 Removal Summary:")
        click.echo(f"   Successfully removed: {total_removed}")
        click.echo(f"   Failed to remove: {total_errors}")
        click.echo(f"   Total processed: {total_removed + total_errors}")
        logger.info(f"Removal summary - Successfully removed: {total_removed}, Failed: {total_errors}")
    
    if total_removed > 0 and not dry_run:
        click.echo("\n✅ Duplicate removal completed.")
        click.echo("You may want to run 'gtasks sync' to ensure consistency.")
        logger.info("Duplicate removal completed successfully")
    elif not dry_run:
        click.echo("\n✅ No duplicates found or removed.")
        logger.info("No duplicates found or removed")