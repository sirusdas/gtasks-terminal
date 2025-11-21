#!/usr/bin/env python3
"""
Common utilities for interactive mode
"""

import click
from collections import defaultdict
from gtasks_cli.models.task import TaskStatus
from gtasks_cli.utils.logger import setup_logger
from rich.console import Console
from rich.panel import Panel

console = Console()
logger = setup_logger(__name__)


def refresh_task_list(task_manager, task_state, use_google_tasks=False):
    """Refresh the task list with incomplete tasks only"""
    if use_google_tasks:
        # For Google Tasks, we need to get tasks grouped by their lists
        from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
        client = GoogleTasksClient()
        tasklists = client.list_tasklists()
        
        tasks = []
        for tasklist in tasklists:
            tasklist_id = tasklist['id']
            tasklist_title = tasklist.get('title', 'Untitled List')
            # Get all tasks and filter for this specific tasklist
            all_tasks = task_manager.list_tasks()
            list_tasks = [t for t in all_tasks if getattr(t, 'tasklist_id', None) == tasklist_id]
            
            # Filter for incomplete tasks
            incomplete_tasks = [t for t in list_tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
            
            # Add list_title to each task for grouping display
            for task in incomplete_tasks:
                task.list_title = tasklist_title
                
            tasks.extend(incomplete_tasks)
    else:
        # For local mode, just get incomplete tasks
        tasks = task_manager.list_tasks()
        logger.debug(f"Loaded {len(tasks)} total tasks")
        for task in tasks:
            logger.debug(f"Task: {task.title} (ID: {task.id}) - Status: {task.status}")
        tasks = [t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]]
        logger.debug(f"Filtered to {len(tasks)} incomplete tasks")
        # Add list_title to each task for grouping display (default to "Tasks" for local mode)
        for task in tasks:
            if not hasattr(task, 'list_title') or not task.list_title:
                task.list_title = "Tasks"
    
    # Display tasks grouped by list names
    from gtasks_cli.commands.interactive_utils.display import display_tasks_grouped_by_list
    displayed_tasks = display_tasks_grouped_by_list(tasks)
    task_state.set_tasks(displayed_tasks)
    return displayed_tasks