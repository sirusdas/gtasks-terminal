"""
Task management for the Google Tasks CLI application.
"""

from typing import List, Optional
from datetime import datetime
import traceback
import uuid
from gtasks_cli.models.task import Task, Priority, TaskStatus
from gtasks_cli.storage.local_storage import LocalStorage
from gtasks_cli.storage.sqlite_storage import SQLiteStorage
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.integrations.sync_manager import SyncManager
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


class TaskManager:
    """Manages tasks and provides high-level task operations."""
    
    def __init__(self, use_google_tasks: bool = False, storage_backend: str = 'json', account_name: str = None):
        """
        Initialize the TaskManager.
        
        Args:
            use_google_tasks: Whether to use Google Tasks API
            storage_backend: Storage backend to use ('json' or 'sqlite')
            account_name: Name of the account for multi-account support
        """
        self.use_google_tasks = use_google_tasks
        self.account_name = account_name
        
        # Initialize storage based on backend and account
        if storage_backend == 'sqlite':
            self.storage = SQLiteStorage(account_name=account_name)
            logger.info(f"Using SQLite storage backend for account: {account_name or 'default'}")
        else:
            self.storage = LocalStorage(account_name=account_name)
            logger.info(f"Using JSON file storage backend for account: {account_name or 'default'}")
        
        logger.debug(f"TaskManager initialized with use_google_tasks={use_google_tasks}, storage_backend={storage_backend}, account_name={account_name}")
        
        # Always initialize Google Tasks client for auto-save support
        # Even in local mode, we may need it for auto-save functionality
        self.google_client = GoogleTasksClient(account_name=account_name)
        
        # Initialize sync manager if using Google Tasks directly
        if use_google_tasks:
            self.sync_manager = SyncManager(self.storage, self.google_client)
            logger.info(f"Google Tasks mode enabled for account: {account_name or 'default'}")
        else:
            logger.info(f"Local mode with auto-save support for account: {account_name or 'default'}")
    
    def create_task(self, title: str, description: Optional[str] = None, 
                   due: Optional[str] = None, priority: Priority = Priority.MEDIUM,
                   project: Optional[str] = None, tags: Optional[List[str]] = None,
                   notes: Optional[str] = None, recurrence_rule: Optional[str] = None,
                   tasklist_name: Optional[str] = None, tasklist_id: Optional[str] = None,
                   estimated_duration: Optional[int] = None) -> Optional[Task]:
        """Create a new task."""
        if self.use_google_tasks:
            # Create task via Google Tasks API
            google_task = self.google_client.create_task(
                title=title,
                description=description,
                due=due,
                priority=priority,
                project=project,
                tags=tags or [],
                notes=notes,
                recurrence_rule=recurrence_rule,
                tasklist_name=tasklist_name,
                tasklist_id=tasklist_id,
                estimated_duration=estimated_duration
            )
            
            if google_task:
                # Convert Google Task to local Task model
                task = Task(
                    id=google_task.id,
                    title=google_task.title,
                    description=google_task.description,
                    due=google_task.due,
                    priority=priority,
                    status=TaskStatus(google_task.status),
                    project=project,
                    tags=tags or [],
                    tasklist_id=google_task.tasklist_id,
                    notes=notes,
                    created_at=google_task.created_at,
                    modified_at=google_task.modified_at,
                    completed_at=google_task.completed_at,
                    estimated_duration=estimated_duration,
                    recurrence_rule=recurrence_rule
                )
                
                # Save to local storage for offline access
                if isinstance(self.storage, SQLiteStorage):
                    self.storage.save_tasks([task.model_dump()])
                else:
                    task_dicts = self.storage.load_tasks()
                    task_dicts.append(task.model_dump())
                    self.storage.save_tasks(task_dicts)
                
                # Update list mapping if needed
                if tasklist_name:
                    list_mapping = self.storage.load_list_mapping()
                    list_mapping[task.id] = tasklist_name
                    self.storage.save_list_mapping(list_mapping)
                
                return task
        else:
            # Create task locally
            task = Task(
                id=str(uuid.uuid4()),
                title=title,
                description=description,
                priority=priority,
                project=project,
                tags=tags or [],
                notes=notes,
                tasklist_id=tasklist_id or "default",
                estimated_duration=estimated_duration,
                recurrence_rule=recurrence_rule
            )
            
            # Parse due date if provided
            if due:
                try:
                    # Try parsing as ISO format
                    task.due = datetime.fromisoformat(due)
                except ValueError:
                    # Handle other date formats as needed
                    logger.warning(f"Could not parse due date: {due}")
            
            # Save to local storage
            if isinstance(self.storage, SQLiteStorage):
                self.storage.save_tasks([task.model_dump()])
            else:
                task_dicts = self.storage.load_tasks()
                task_dicts.append(task.model_dump())
                self.storage.save_tasks(task_dicts)
            
            # Update list mapping if needed
            if tasklist_name:
                list_mapping = self.storage.load_list_mapping()
                list_mapping[task.id] = tasklist_name
                self.storage.save_list_mapping(list_mapping)
            
            return task
    
    def list_tasks(self, list_filter: Optional[str] = None, 
                  status: Optional[TaskStatus] = None,
                  priority: Optional[Priority] = None,
                  project: Optional[str] = None,
                  recurring: Optional[bool] = None,
                  search: Optional[str] = None) -> List[Task]:
        """List tasks with optional filtering."""
        if self.use_google_tasks:
            # Get tasks from Google Tasks API
            google_tasks = self.google_client.list_tasks()
            
            # Convert to local Task models
            tasks = []
            for google_task in google_tasks:
                try:
                    # Get tasklist title for display
                    tasklist_title = self.google_client.get_tasklist_title(google_task.tasklist_id)
                    
                    task = Task(
                        id=google_task.id,
                        title=google_task.title,
                        description=google_task.description,
                        due=google_task.due,
                        priority=Priority.MEDIUM,  # Default since Google Tasks doesn't have priority
                        status=TaskStatus(google_task.status),
                        project=None,  # Not supported in basic Google Tasks
                        tags=[],  # Not supported in basic Google Tasks
                        tasklist_id=google_task.tasklist_id,
                        notes=google_task.notes,
                        created_at=google_task.created_at,
                        modified_at=google_task.modified_at,
                        completed_at=google_task.completed_at,
                        position=google_task.position
                    )
                    
                    # Set the list title for display
                    task.list_title = tasklist_title
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Error converting Google Task {google_task.id}: {e}")
                    continue
            
            logger.debug(f"Loaded {len(tasks)} tasks from Google Tasks")
            return tasks
        else:
            # In local mode, get tasks from local storage
            task_dicts = self.storage.load_tasks()
            logger.debug(f"Loaded {len(task_dicts)} task dictionaries from storage")
            tasks = [Task(**task_dict) for task_dict in task_dicts]
            logger.debug(f"Converted to {len(tasks)} Task objects")

            # Load list mapping and set list_title on each task
            list_mapping = self.storage.load_list_mapping()
            for task in tasks:
                task.list_title = list_mapping.get(task.id, 'Tasks')
            
            # Apply list filter for local mode
            if list_filter:
                tasks = [t for t in tasks if t.list_title and list_filter.lower() in t.list_title.lower()]
            
            # Apply other filters
            filtered_tasks = []
            for task in tasks:
                # Status filter
                if status and task.status != status:
                    continue
                
                # Priority filter
                if priority and task.priority != priority:
                    continue
                
                # Project filter
                if project and task.project != project:
                    continue
                
                # Recurring filter
                if recurring is not None:
                    if recurring and not task.is_recurring:
                        continue
                    elif not recurring and task.is_recurring:
                        continue
                
                # Search filter with multi-search support
                if search:
                    # Split search terms by pipe separator for multi-search
                    search_terms = [term.strip() for term in search.split('|') if term.strip()]
                    match_found = False
                    
                    # Check if any of the search terms match
                    for term in search_terms:
                        term_lower = term.lower()
                        if (term_lower in task.title.lower() or 
                            (task.description and term_lower in task.description.lower()) or
                            (task.notes and term_lower in task.notes.lower())):
                            match_found = True
                            break
                    
                    # If no search term matches, skip this task
                    if not match_found:
                        continue
                
                filtered_tasks.append(task)
            
            logger.debug(f"Filtered to {len(filtered_tasks)} tasks")
            return filtered_tasks
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID."""
        if self.use_google_tasks:
            # Get task from Google Tasks API
            google_task = self.google_client.get_task(task_id)
            if google_task:
                # Convert to local Task model
                task = Task(
                    id=google_task.id,
                    title=google_task.title,
                    description=google_task.description,
                    due=google_task.due,
                    priority=Priority.MEDIUM,
                    status=TaskStatus(google_task.status),
                    project=None,
                    tags=[],
                    tasklist_id=google_task.tasklist_id,
                    notes=google_task.notes,
                    created_at=google_task.created_at,
                    modified_at=google_task.modified_at,
                    completed_at=google_task.completed_at
                )
                return task
        else:
            # Get task from local storage
            tasks = self.list_tasks()
            for task in tasks:
                if task.id == task_id:
                    return task
        
        return None
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update a task with given attributes."""
        if self.use_google_tasks:
            # Update via Google Tasks API
            success = self.google_client.update_task(task_id, **kwargs)
            if success:
                # Also update local storage
                tasks = self.list_tasks()
                for task in tasks:
                    if task.id == task_id:
                        # Update the task attributes
                        for key, value in kwargs.items():
                            if hasattr(task, key):
                                setattr(task, key, value)
                        
                        # Save updated tasks to local storage
                        if isinstance(self.storage, SQLiteStorage):
                            self.storage.save_tasks([task.model_dump()])
                        else:
                            task_dicts = [t.model_dump() for t in tasks]
                            self.storage.save_tasks(task_dicts)
                        break
            return success
        else:
            # Update in local storage
            # Get tasks from storage
            task_dicts = self.storage.load_tasks()
            tasks = [Task(**task_dict) for task_dict in task_dicts]
            
            # Find and update the specific task
            for task in tasks:
                if task.id == task_id:
                    # Update the task attributes
                    for key, value in kwargs.items():
                        if hasattr(task, key):
                            setattr(task, key, value)
                    
                    # Update modified timestamp
                    task.modified_at = datetime.utcnow()
                    
                    # Save updated tasks to local storage
                    if isinstance(self.storage, SQLiteStorage):
                        self.storage.save_tasks([task.model_dump()])
                    else:
                        task_dicts = [t.model_dump() for t in tasks]
                        self.storage.save_tasks(task_dicts)
                    return True
            
            return False
    
    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        if self.use_google_tasks:
            # Complete via Google Tasks API
            success = self.google_client.complete_task(task_id)
            if success:
                # Also update local storage
                task = self.get_task(task_id)
                if task:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    # Save updated task to local storage
                    if isinstance(self.storage, SQLiteStorage):
                        self.storage.save_tasks([task.model_dump()])
                    else:
                        tasks = self.list_tasks()
                        task_dicts = [t.model_dump() for t in tasks]
                        self.storage.save_tasks(task_dicts)
            return success
        else:
            # Complete in local storage
            # Get tasks from storage
            task_dicts = self.storage.load_tasks()
            tasks = [Task(**task_dict) for task_dict in task_dicts]
            
            # Find and update the specific task
            for task in tasks:
                if task.id == task_id:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    task.modified_at = datetime.utcnow()
                    
                    # Save updated tasks to local storage
                    if isinstance(self.storage, SQLiteStorage):
                        self.storage.save_tasks([task.model_dump()])
                    else:
                        task_dicts = [t.model_dump() for t in tasks]
                        self.storage.save_tasks(task_dicts)
                    return True
            
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task (mark as deleted)."""
        if self.use_google_tasks:
            # Delete via Google Tasks API
            success = self.google_client.delete_task(task_id)
            if success:
                # Also update local storage
                task = self.get_task(task_id)
                if task:
                    task.status = TaskStatus.DELETED
                    task.modified_at = datetime.utcnow()
                    # Save updated task to local storage
                    if isinstance(self.storage, SQLiteStorage):
                        self.storage.save_tasks([task.model_dump()])
                    else:
                        tasks = self.list_tasks()
                        task_dicts = [t.model_dump() for t in tasks]
                        self.storage.save_tasks(task_dicts)
            return success
        else:
            # Delete in local storage
            task = self.get_task(task_id)
            if task:
                task.status = TaskStatus.DELETED
                task.modified_at = datetime.utcnow()
                
                # Save updated task to local storage
                if isinstance(self.storage, SQLiteStorage):
                    self.storage.save_tasks([task.model_dump()])
                else:
                    tasks = self.list_tasks()
                    task_dicts = [t.model_dump() for t in tasks]
                    self.storage.save_tasks(task_dicts)
                return True
            
            return False
    
    def sync_with_google_tasks(self) -> bool:
        """Synchronize tasks between local storage and Google Tasks."""
        if not self.use_google_tasks:
            logger.warning("Google Tasks sync requested but not enabled")
            return False
        
        try:
            success = self.sync_manager.sync()
            logger.info(f"Sync completed: {'success' if success else 'failed'}")
            return success
        except Exception as e:
            logger.error(f"Sync failed with error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False