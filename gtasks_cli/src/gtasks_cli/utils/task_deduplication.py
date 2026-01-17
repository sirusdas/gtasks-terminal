"""
Utility functions for task deduplication and duplicate checking.
"""

import hashlib
import logging
from typing import Set, Optional
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)


def _format_date_for_signature(date_str: str) -> str:
    """
    Format a date consistently for signature creation.
    
    Args:
        date_str: Date string to format
        
    Returns:
        Formatted date string
    """
    if not date_str or date_str == "None":
        return ""
    
    try:
        # Parse the date
        if isinstance(date_str, str):
            # Handle string dates
            try:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, try another format
                date = datetime.fromisoformat(date_str)
        elif isinstance(date_str, datetime):
            # Already a datetime object
            date = date_str
        else:
            # Some other type, convert to string first
            date = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
        
        # Format consistently without microseconds to match Google Tasks storage format
        return date.strftime('%Y-%m-%d %H:%M:%S%z')
    except Exception as e:
        logger.warning(f"Failed to format date '{date_str}': {e}")
        return str(date_str)


def create_task_signature(title: str, description: str = "", created_date: str = "", status: str = "") -> str:
    """
    Create a unique signature for a task based on its key attributes.
    Uses created_date (stable) instead of due_date (changes for recurring tasks).
    
    Args:
        title: Task title
        description: Task description
        created_date: Task creation date (stable for recurring tasks)
        status: Task status
        
    Returns:
        MD5 hash of the task signature
    """
    # Format created date consistently
    formatted_created_date = _format_date_for_signature(created_date)
    
    signature_string = f"{title}|{description}|{formatted_created_date}|{status}"
    signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
    logger.debug(f"Created signature '{signature}' for task: {title}|{description}|{formatted_created_date}|{status}")
    return signature


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
            # Use created_at (stable) instead of due (changes for recurring tasks)
            created_at = task_data.get('created_at', '') or task_data.get('due', '')
            status = task_data.get('status', '')
            signature = create_task_signature(title, description, created_at, status)
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
                        # Use created_at (stable) instead of due (changes for recurring tasks)
                        created_at = task.created_at or task.due or ''
                        status = str(task.status.value) if hasattr(task.status, 'value') else str(task.status)
                        signature = create_task_signature(title, description, created_at, status)
                        signatures.add(signature)
            else:
                print("Warning: Could not connect to Google Tasks to check existing tasks")
        except Exception as e:
            print(f"Warning: Could not check Google Tasks for existing tasks: {e}")
    
    return signatures


def is_task_duplicate(task_title: str, 
                     task_description: str = "", 
                     task_created_date: str = "", 
                     task_status: str = "",
                     existing_signatures: Optional[Set[str]] = None,
                     use_google_tasks: bool = True) -> bool:
    """
    Check if a task is already present (duplicate) in either local storage or Google Tasks.
    
    Args:
        task_title: Title of the task to check
        task_description: Description of the task to check
        task_created_date: Created date of the task to check (stable for recurring tasks)
        task_status: Status of the task to check
        existing_signatures: Pre-computed set of existing task signatures (optional)
        use_google_tasks: Whether to check Google Tasks for existing tasks
        
    Returns:
        True if task is duplicate, False otherwise
    """
    # Create signature for the task to check
    task_signature = create_task_signature(
        title=task_title, 
        description=task_description, 
        created_date=task_created_date, 
        status=task_status
    )
    logger.debug(f"Checking for duplicate with signature: {task_signature}")
    
    # Use provided signatures or get fresh ones
    if existing_signatures is not None:
        signatures = existing_signatures
        logger.debug(f"Using provided signatures set with {len(signatures)} items")
    else:
        signatures = get_existing_task_signatures(use_google_tasks)
        logger.debug(f"Retrieved fresh signatures set with {len(signatures)} items")
    
    # Check if task already exists
    is_duplicate = task_signature in signatures
    logger.debug(f"Task is duplicate: {is_duplicate}")
    return is_duplicate


def check_and_add_task(task_title: str,
                      task_description: str = "",
                      task_created_date: str = "",
                      task_status: str = "",
                      add_task_function=None,
                      *args, **kwargs) -> bool:
    """
    Check if a task is duplicate and add it only if it's not.
    
    Args:
        task_title: Title of the task to add
        task_description: Description of the task to add
        task_created_date: Created date of the task to add (stable for recurring tasks)
        task_status: Status of the task to add
        add_task_function: Function to call to add the task if not duplicate
        *args: Additional positional arguments to pass to add_task_function
        **kwargs: Additional keyword arguments to pass to add_task_function
        
    Returns:
        True if task was added, False if it was duplicate or addition failed
    """
    # Check if task already exists
    if is_task_duplicate(task_title, task_description, task_created_date, task_status):
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