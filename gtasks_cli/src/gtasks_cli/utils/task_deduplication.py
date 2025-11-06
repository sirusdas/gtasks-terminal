"""
Utility functions for task deduplication and duplicate checking.
"""

import hashlib
from typing import Set, Optional


def create_task_signature(title: str, description: str = "", due_date: str = "", status: str = "") -> str:
    """
    Create a unique signature for a task based on its key attributes.
    
    Args:
        title: Task title
        description: Task description
        due_date: Task due date
        status: Task status
        
    Returns:
        MD5 hash of the task signature
    """
    signature_string = f"{title}|{description}|{due_date}|{status}"
    return hashlib.md5(signature_string.encode('utf-8')).hexdigest()


def get_existing_task_signatures(use_google_tasks: bool = True) -> Set[str]:
    """
    Get signatures of all existing tasks from both local storage and Google Tasks.
    
    Args:
        use_google_tasks: Whether to check Google Tasks for existing tasks
        
    Returns:
        Set of task signatures
    """
    signatures = set()
    
    # Check local storage
    try:
        from gtasks_cli.storage.local_storage import LocalStorage
        storage = LocalStorage()
        tasks = storage.load_tasks()
        
        for task_data in tasks:
            title = task_data.get('title', '')
            description = task_data.get('description', '')
            due = str(task_data.get('due', ''))
            status = task_data.get('status', '')
            signature = create_task_signature(title, description, due, status)
            signatures.add(signature)
    except Exception as e:
        print(f"Warning: Could not check local storage for existing tasks: {e}")
    
    # Check Google Tasks if requested
    if use_google_tasks:
        try:
            from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
            client = GoogleTasksClient()
            if client.connect():
                # Get all task lists
                tasklists = client.list_tasklists()
                
                for tasklist in tasklists:
                    tasklist_id = tasklist['id']
                    
                    # Get all active tasks from this list
                    active_tasks = client.list_tasks(
                        tasklist_id=tasklist_id,
                        show_completed=True,
                        show_hidden=True,
                        show_deleted=False
                    )
                    
                    for task in active_tasks:
                        title = task.title or ''
                        description = task.description or ''
                        due_date = str(task.due) if task.due else ''
                        status = str(task.status.value) if hasattr(task.status, 'value') else str(task.status)
                        signature = create_task_signature(title, description, due_date, status)
                        signatures.add(signature)
            else:
                print("Warning: Could not connect to Google Tasks to check existing tasks")
        except Exception as e:
            print(f"Warning: Could not check Google Tasks for existing tasks: {e}")
    
    return signatures


def is_task_duplicate(task_title: str, 
                     task_description: str = "", 
                     task_due_date: str = "", 
                     task_status: str = "",
                     existing_signatures: Optional[Set[str]] = None,
                     use_google_tasks: bool = True) -> bool:
    """
    Check if a task is already present (duplicate) in either local storage or Google Tasks.
    
    Args:
        task_title: Title of the task to check
        task_description: Description of the task to check
        task_due_date: Due date of the task to check
        task_status: Status of the task to check
        existing_signatures: Pre-computed set of existing task signatures (optional)
        use_google_tasks: Whether to check Google Tasks for existing tasks
        
    Returns:
        True if task is duplicate, False otherwise
    """
    # Create signature for the task to check
    task_signature = create_task_signature(task_title, task_description, task_due_date, task_status)
    
    # Use provided signatures or get fresh ones
    if existing_signatures is not None:
        signatures = existing_signatures
    else:
        signatures = get_existing_task_signatures(use_google_tasks)
    
    # Check if task already exists
    return task_signature in signatures


def check_and_add_task(task_title: str,
                      task_description: str = "",
                      task_due_date: str = "",
                      task_status: str = "",
                      add_task_function=None,
                      *args, **kwargs) -> bool:
    """
    Check if a task is duplicate and add it only if it's not.
    
    Args:
        task_title: Title of the task to add
        task_description: Description of the task to add
        task_due_date: Due date of the task to add
        task_status: Status of the task to add
        add_task_function: Function to call to add the task if not duplicate
        *args: Additional positional arguments to pass to add_task_function
        **kwargs: Additional keyword arguments to pass to add_task_function
        
    Returns:
        True if task was added, False if it was duplicate or addition failed
    """
    # Check if task already exists
    if is_task_duplicate(task_title, task_description, task_due_date, task_status):
        print(f"Task '{task_title}' already exists. Skipping.")
        return False
    
    # Add the task if not duplicate
    if add_task_function:
        try:
            result = add_task_function(*args, **kwargs)
            if result:
                # Update signatures to prevent future duplicates in the same session
                return True
            else:
                print(f"Failed to add task '{task_title}'")
                return False
        except Exception as e:
            print(f"Error adding task '{task_title}': {e}")
            return False
    else:
        print("No function provided to add the task")
        return False