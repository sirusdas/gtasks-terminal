#!/usr/bin/env python3
"""
Maintenance script for deduplicating Google Tasks
"""

import sys
import os
import time
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
import hashlib
from collections import defaultdict


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


def deduplicate_tasks(dry_run=False):
    """Remove duplicate tasks from all task lists"""
    logger.info("Starting deduplication process")
    
    if dry_run:
        logger.info("Running in dry-run mode - no tasks will be deleted")
    else:
        logger.info("Running in actual removal mode")
    
    # Connect to Google Tasks
    google_client = GoogleTasksClient()
    if not google_client.connect():
        logger.error("Failed to connect to Google Tasks")
        return False
    
    logger.info("Connected to Google Tasks API")
    
    # Get all task lists
    tasklists = google_client.list_tasklists()
    logger.info(f"Found {len(tasklists)} task lists")
    
    total_duplicates = 0
    total_removed = 0
    total_errors = 0
    
    for tasklist in tasklists:
        tasklist_id = tasklist['id']
        tasklist_title = tasklist['title']
        
        logger.info(f"Processing '{tasklist_title}' list...")
        
        # Get all tasks (including deleted) from this list
        all_tasks = google_client.list_tasks(
            tasklist_id=tasklist_id,
            show_completed=True,
            show_hidden=True,
            show_deleted=True
        )
        
        logger.info(f"  Total tasks in list: {len(all_tasks)}")
        
        # Group tasks by signature
        task_groups = defaultdict(list)
        for task in all_tasks:
            signature = create_task_signature(task)
            task_groups[signature].append(task)
        
        logger.info(f"  Grouped tasks into {len(task_groups)} signature groups")
        
        # Find duplicates (groups with more than one task)
        duplicates = []
        duplicate_groups = 0
        for signature, tasks in task_groups.items():
            if len(tasks) > 1:
                logger.info(f"  Found duplicate group with {len(tasks)} tasks")
                duplicate_groups += 1
                # Sort by modification date to keep the most recent one
                tasks.sort(key=lambda t: t.modified_at or t.created_at, reverse=True)
                # Keep the first (most recent) and mark others for deletion
                duplicates.extend(tasks[1:])
        
        logger.info(f"  Found {len(duplicates)} duplicate tasks in {duplicate_groups} groups")
        total_duplicates += len(duplicates)
        
        if duplicates and not dry_run:
            logger.info("  Removing duplicates:")
            removed_count = 0
            failed_count = 0
            
            for task in duplicates:
                try:
                    logger.info(f"    Deleting task: {task.title} (ID: {task.id})")
                    # Delete the task
                    success = google_client.delete_task(task.id, tasklist_id=tasklist_id)
                    if success:
                        logger.info(f"    Successfully deleted task: {task.title}")
                        removed_count += 1
                    else:
                        logger.warning(f"    Failed to delete task: {task.title}")
                        failed_count += 1
                except Exception as e:
                    logger.error(f"    Failed to remove {task.title}: {e}")
                    failed_count += 1
            
            logger.info(f"  Removed: {removed_count}, Failed: {failed_count}")
            total_removed += removed_count
            total_errors += failed_count
        elif duplicates and dry_run:
            logger.info("  Duplicates found (dry-run mode):")
            for i, task in enumerate(duplicates):
                mod_date = task.modified_at or task.created_at
                logger.info(f"    {i+1}. {task.title} (ID: {task.id}, Modified: {mod_date})")
        else:
            logger.info("  No duplicates found in this list")
    
    # Summary
    if dry_run:
        logger.info("Dry-run summary:")
        logger.info(f"  Total duplicate tasks found: {total_duplicates}")
    else:
        logger.info("Removal summary:")
        logger.info(f"  Total duplicate tasks found: {total_duplicates}")
        logger.info(f"  Successfully removed: {total_removed}")
        logger.info(f"  Failed to remove: {total_errors}")
    
    if total_duplicates > 0 and not dry_run:
        logger.info("Duplicate removal completed.")
    elif not dry_run:
        logger.info("No duplicates found or removed.")
    
    return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deduplicate Google Tasks")
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Preview changes without actually making them'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        success = deduplicate_tasks(dry_run=args.dry_run)
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Error during deduplication: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())