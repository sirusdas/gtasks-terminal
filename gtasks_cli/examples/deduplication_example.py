#!/usr/bin/env python3
"""
Example script demonstrating how to use the task deduplication utility
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gtasks_cli.utils.task_deduplication import is_task_duplicate, check_and_add_task
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient


def example_add_task_function(title, description="", due_date=""):
    """
    Example function to add a task - this would be replaced with your actual task creation logic
    """
    print(f"Adding task: {title}")
    # In a real implementation, this would call your task creation API
    # For this example, we'll just simulate success
    return True


def main():
    print("Task Deduplication Utility Example")
    print("=" * 40)
    
    # Example 1: Check if a task is duplicate
    task_title = "Example Task"
    task_description = "This is an example task"
    task_due_date = "2025-12-31"
    
    if is_task_duplicate(task_title, task_description, task_due_date, "pending"):
        print(f"Task '{task_title}' already exists!")
    else:
        print(f"Task '{task_title}' does not exist yet.")
    
    # Example 2: Check and add task only if not duplicate
    print("\nChecking and adding task...")
    result = check_and_add_task(
        task_title="Another Example Task",
        task_description="This is another example task",
        task_due_date="2025-11-30",
        task_status="pending",
        add_task_function=example_add_task_function,
        title="Another Example Task",
        description="This is another example task",
        due_date="2025-11-30"
    )
    
    if result:
        print("Task was added successfully")
    else:
        print("Task was not added (either duplicate or failed to add)")


if __name__ == "__main__":
    main()