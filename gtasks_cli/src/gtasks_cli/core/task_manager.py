"""
Task management functionality for the Google Tasks CLI application.
"""

from typing import List, Optional
from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.storage.local_storage import LocalStorage
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.integrations.sync_manager import SyncManager
from datetime import datetime

logger = setup_logger(__name__)


class TaskManager:
    """Manages task operations in the Google Tasks CLI application."""
    
    def __init__(self, use_google_tasks: bool = False):
        """
        Initialize the TaskManager.
        
        Args:
            use_google_tasks: Whether to use Google Tasks API instead of local storage
        """
        self.use_google_tasks = use_google_tasks
        if use_google_tasks:
            self.google_client = GoogleTasksClient()
            self.sync_manager = SyncManager()
        else:
            self.storage = LocalStorage()
        logger.debug(f"TaskManager initialized with {'Google Tasks' if use_google_tasks else 'local storage'}")
    
    def create_task(self, title: str, description: Optional[str] = None, 
                   due: Optional[str] = None, priority: Priority = Priority.MEDIUM,
                   project: Optional[str] = None, tags: Optional[List[str]] = None,
                   tasklist_id: str = "default", notes: Optional[str] = None,
                   dependencies: Optional[List[str]] = None,
                   recurrence_rule: Optional[str] = None) -> Task:
        """
        Create a new task.
        
        Args:
            title: Task title
            description: Task description
            due: Due date (ISO format string)
            priority: Task priority
            project: Project name
            tags: List of tags
            tasklist_id: Tasklist ID
            notes: Task notes
            dependencies: List of task IDs this task depends on
            recurrence_rule: Recurrence rule (RRULE format)
            
        Returns:
            Task: Created task object
        """
        if self.use_google_tasks:
            # For Google Tasks, we need to first create a local task, then sync to Google
            import uuid
            task_id = str(uuid.uuid4())
            
            # Convert due date string to datetime if provided
            from datetime import datetime
            due_date = None
            if due:
                try:
                    due_date = datetime.fromisoformat(due)
                except ValueError:
                    logger.warning(f"Invalid due date format: {due}")
            
            task = Task(
                id=task_id,
                title=title,
                description=description,
                due=due_date,
                priority=priority,
                project=project,
                tags=tags or [],
                tasklist_id=tasklist_id,
                notes=notes,
                dependencies=dependencies or [],
                recurrence_rule=recurrence_rule,
                is_recurring=bool(recurrence_rule)
            )
            
            # Try to sync with Google Tasks
            if self.sync_manager.is_connected():
                google_task = self.google_client.create_task(task)
                if google_task:
                    # Save locally as well for offline access
                    tasks = self._load_tasks()
                    tasks.append(google_task)
                    self._save_tasks(tasks)
                    return google_task
            
            # If Google sync failed, save locally and mark for sync later
            tasks = self._load_tasks()
            tasks.append(task)
            self._save_tasks(tasks)
            logger.warning("Created task locally, will sync with Google Tasks when online")
            return task
        else:
            # Load existing tasks
            tasks = self._load_tasks()
            
            # Generate a simple ID for now (in real implementation, this would come from API)
            import uuid
            task_id = str(uuid.uuid4())
            
            # Convert due date string to datetime if provided
            from datetime import datetime
            due_date = None
            if due:
                try:
                    due_date = datetime.fromisoformat(due)
                except ValueError:
                    logger.warning(f"Invalid due date format: {due}")
            
            task = Task(
                id=task_id,
                title=title,
                description=description,
                due=due_date,
                priority=priority,
                project=project,
                tags=tags or [],
                tasklist_id=tasklist_id,
                notes=notes,
                dependencies=dependencies or [],
                recurrence_rule=recurrence_rule,
                is_recurring=bool(recurrence_rule)
            )
            
            tasks.append(task)
            self._save_tasks(tasks)
            logger.info(f"Created task: {task_id} - {title}")
            return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task: Task object if found, None otherwise
        """
        if self.use_google_tasks:
            # For offline support, try local storage first
            tasks = self._load_tasks()
            for task in tasks:
                if task.id == task_id:
                    logger.debug(f"Found task in local storage: {task_id}")
                    return task
            
            # If not found locally and we're online, try Google Tasks
            if self.sync_manager.is_connected():
                task = self.google_client.get_task(task_id)
                if task:
                    # Cache it locally for offline access
                    tasks = self._load_tasks()
                    # Remove existing task with same ID if present
                    tasks = [t for t in tasks if t.id != task_id]
                    tasks.append(task)
                    self._save_tasks(tasks)
                    return task
            
            return None
        else:
            tasks = self._load_tasks()
            for task in tasks:
                if task.id == task_id:
                    logger.debug(f"Found task: {task_id}")
                    return task
            
            logger.warning(f"Task not found: {task_id}")
            return None
    
    def list_tasks(self, status: Optional[TaskStatus] = None, 
                  priority: Optional[Priority] = None,
                  project: Optional[str] = None) -> List[Task]:
        """
        List tasks with optional filtering.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            project: Filter by project
            
        Returns:
            List[Task]: List of tasks matching criteria
        """
        if self.use_google_tasks:
            # For offline support, use sync manager to get tasks
            tasks = self.sync_manager.get_offline_tasks()
            
            # If online, try to sync to get latest data
            if self.sync_manager.is_connected():
                self.sync_manager.sync()
                tasks = self.sync_manager.get_offline_tasks()
        else:
            tasks = self._load_tasks()
        
        filtered_tasks = tasks
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t.status == status]
            
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t.priority == priority]
            
        if project:
            filtered_tasks = [t for t in filtered_tasks if t.project == project]
            
        logger.debug(f"Listed {len(filtered_tasks)} tasks")
        return filtered_tasks
    
    def search_tasks(self, query: str) -> List[Task]:
        """
        Search tasks by query string.
        
        Args:
            query: Search query string
            
        Returns:
            List[Task]: List of tasks matching the query
        """
        if self.use_google_tasks:
            # For offline support, use sync manager to get tasks
            tasks = self.sync_manager.get_offline_tasks()
            
            # If online, try to sync to get latest data
            if self.sync_manager.is_connected():
                self.sync_manager.sync()
                tasks = self.sync_manager.get_offline_tasks()
        else:
            tasks = self._load_tasks()
        
        # Convert query to lowercase for case-insensitive search
        query_lower = query.lower()
        
        # Search in title, description, project, tags, and notes
        matching_tasks = []
        for task in tasks:
            # Skip deleted tasks
            if task.status == TaskStatus.DELETED:
                continue
                
            # Check if query matches any field
            if (query_lower in (task.title or "").lower() or 
                query_lower in (task.description or "").lower() or
                query_lower in (task.project or "").lower() or
                any(query_lower in (tag or "").lower() for tag in task.tags) or
                query_lower in (task.notes or "").lower()):
                matching_tasks.append(task)
        
        logger.debug(f"Found {len(matching_tasks)} tasks matching query: {query}")
        return matching_tasks
    
    def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        """
        Update a task with given fields.
        
        Args:
            task_id: Task ID
            **kwargs: Fields to update
            
        Returns:
            Task: Updated task object if found, None otherwise
        """
        if self.use_google_tasks:
            # Get the existing task
            task = self.get_task(task_id)
            if not task:
                return None
            
            # Update the task with new values
            for field, value in kwargs.items():
                if hasattr(task, field):
                    # Special handling for due date
                    if field == 'due' and isinstance(value, str):
                        from datetime import datetime
                        try:
                            value = datetime.fromisoformat(value)
                        except ValueError:
                            logger.warning(f"Invalid due date format: {value}")
                            continue
                    setattr(task, field, value)
            
            from datetime import datetime
            task.modified_at = kwargs.get('modified_at', datetime.utcnow())
            
            # Try to sync with Google Tasks
            if self.sync_manager.is_connected():
                updated_task = self.google_client.update_task(task)
                if updated_task:
                    # Update local cache
                    tasks = self._load_tasks()
                    # Remove existing task with same ID if present
                    tasks = [t for t in tasks if t.id != task_id]
                    tasks.append(updated_task)
                    self._save_tasks(tasks)
                    return updated_task
            
            # If Google sync failed, save locally and mark for sync later
            tasks = self._load_tasks()
            # Remove existing task with same ID if present
            tasks = [t for t in tasks if t.id != task_id]
            tasks.append(task)
            self._save_tasks(tasks)
            logger.warning("Updated task locally, will sync with Google Tasks when online")
            return task
        else:
            tasks = self._load_tasks()
            task = None
            for t in tasks:
                if t.id == task_id:
                    task = t
                    break
                    
            if not task:
                return None
                
            # Update allowed fields
            updatable_fields = {
                'title', 'description', 'due', 'priority', 'status',
                'project', 'tags', 'notes', 'estimated_duration', 'dependencies',
                'recurrence_rule', 'is_recurring'
            }
            
            for field, value in kwargs.items():
                if field in updatable_fields:
                    # Special handling for due date
                    if field == 'due' and isinstance(value, str):
                        from datetime import datetime
                        try:
                            value = datetime.fromisoformat(value)
                        except ValueError:
                            logger.warning(f"Invalid due date format: {value}")
                            continue
                            
                    setattr(task, field, value)
                    
            from datetime import datetime
            task.modified_at = kwargs.get('modified_at', datetime.utcnow())
            
            self._save_tasks(tasks)
            logger.info(f"Updated task: {task_id}")
            return task
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task (mark as deleted).
        
        Args:
            task_id: Task ID
            
        Returns:
            bool: True if task was deleted, False if not found
        """
        if self.use_google_tasks:
            # Try to delete from Google Tasks
            if self.sync_manager.is_connected():
                success = self.google_client.delete_task(task_id)
                if success:
                    # Also mark as deleted locally
                    tasks = self._load_tasks()
                    for task in tasks:
                        if task.id == task_id:
                            task.status = TaskStatus.DELETED
                            from datetime import datetime
                            task.modified_at = datetime.utcnow()
                            self._save_tasks(tasks)
                            logger.info(f"Deleted task: {task_id}")
                            return True
            
            # If Google sync failed, mark as deleted locally and mark for sync later
            tasks = self._load_tasks()
            for task in tasks:
                if task.id == task_id:
                    task.status = TaskStatus.DELETED
                    from datetime import datetime
                    task.modified_at = datetime.utcnow()
                    self._save_tasks(tasks)
                    logger.warning("Deleted task locally, will sync with Google Tasks when online")
                    return True
            
            return False
        else:
            tasks = self._load_tasks()
            task = None
            for t in tasks:
                if t.id == task_id:
                    task = t
                    break
                    
            if not task:
                return False
                
            task.status = TaskStatus.DELETED
            from datetime import datetime
            task.modified_at = datetime.utcnow()
            
            self._save_tasks(tasks)
            logger.info(f"Deleted task: {task_id}")
            return True
    
    def complete_task(self, task_id: str) -> bool:
        """
        Mark a task as completed.
        
        Args:
            task_id: Task ID
            
        Returns:
            bool: True if task was completed, False if not found
        """
        if self.use_google_tasks:
            # Try to complete in Google Tasks
            if self.sync_manager.is_connected():
                success = self.google_client.complete_task(task_id)
                if success:
                    # Also mark as completed locally
                    tasks = self._load_tasks()
                    for task in tasks:
                        if task.id == task_id:
                            task.status = TaskStatus.COMPLETED
                            from datetime import datetime
                            task.completed_at = datetime.utcnow()
                            task.modified_at = datetime.utcnow()
                            self._save_tasks(tasks)
                            logger.info(f"Completed task: {task_id}")
                            return True
            
            # If Google sync failed, mark as completed locally and mark for sync later
            tasks = self._load_tasks()
            for task in tasks:
                if task.id == task_id:
                    task.status = TaskStatus.COMPLETED
                    from datetime import datetime
                    task.completed_at = datetime.utcnow()
                    task.modified_at = datetime.utcnow()
                    self._save_tasks(tasks)
                    logger.warning("Completed task locally, will sync with Google Tasks when online")
                    return True
            
            return False
        else:
            tasks = self._load_tasks()
            task = None
            for t in tasks:
                if t.id == task_id:
                    task = t
                    break
                    
            if not task:
                return False
                
            # Check if task has unmet dependencies
            if not self._can_complete_task(task, tasks):
                logger.warning(f"Cannot complete task {task_id} due to unmet dependencies")
                return False
                
            # Handle recurring tasks
            if task.is_recurring and task.recurrence_rule:
                # Create a new instance of the recurring task
                self._create_next_recurring_task(task)
                
            task.status = TaskStatus.COMPLETED
            from datetime import datetime
            task.completed_at = datetime.utcnow()
            task.modified_at = datetime.utcnow()
            
            self._save_tasks(tasks)
            logger.info(f"Completed task: {task_id}")
            return True
    
    def _create_next_recurring_task(self, recurring_task: Task) -> Optional[Task]:
        """
        Create the next instance of a recurring task.
        
        Args:
            recurring_task: The recurring task template
            
        Returns:
            Task: The newly created task instance, or None if failed
        """
        try:
            import uuid
            from datetime import datetime, timedelta
            
            # Create a new task instance based on the recurring task
            new_task_id = str(uuid.uuid4())
            
            # Calculate next due date based on recurrence rule
            next_due = self._calculate_next_due_date(recurring_task)
            
            new_task = Task(
                id=new_task_id,
                title=recurring_task.title,
                description=recurring_task.description,
                due=next_due,
                priority=recurring_task.priority,
                status=TaskStatus.PENDING,
                project=recurring_task.project,
                tags=recurring_task.tags,
                tasklist_id=recurring_task.tasklist_id,
                notes=recurring_task.notes,
                recurrence_rule=recurring_task.recurrence_rule,
                is_recurring=True,
                recurring_task_id=recurring_task.id,
                created_at=datetime.utcnow(),
                modified_at=datetime.utcnow()
            )
            
            # Add to tasks list
            tasks = self._load_tasks()
            tasks.append(new_task)
            self._save_tasks(tasks)
            
            logger.info(f"Created next instance of recurring task: {new_task_id}")
            return new_task
        except Exception as e:
            logger.error(f"Failed to create next instance of recurring task: {e}")
            return None
    
    def _calculate_next_due_date(self, recurring_task: Task) -> Optional[datetime]:
        """
        Calculate the next due date for a recurring task.
        
        Args:
            recurring_task: The recurring task
            
        Returns:
            datetime: The next due date, or None if unable to calculate
        """
        if not recurring_task.due or not recurring_task.recurrence_rule:
            return None
            
        try:
            # Parse simple recurrence rules
            rule = recurring_task.recurrence_rule.lower()
            current_due = recurring_task.due
            
            if 'daily' in rule:
                return current_due + timedelta(days=1)
            elif 'weekly' in rule:
                return current_due + timedelta(weeks=1)
            elif 'monthly' in rule:
                # Simple monthly increment (doesn't handle month-end edge cases)
                month = current_due.month + 1
                year = current_due.year
                if month > 12:
                    month = 1
                    year += 1
                return current_due.replace(month=month, year=year)
            elif 'yearly' in rule:
                return current_due.replace(year=current_due.year + 1)
            else:
                # Try to parse specific intervals like "every 2 days"
                import re
                match = re.search(r'every\s+(\d+)\s+(day|week|month|year)', rule)
                if match:
                    interval = int(match.group(1))
                    unit = match.group(2)
                    
                    if unit == 'day':
                        return current_due + timedelta(days=interval)
                    elif unit == 'week':
                        return current_due + timedelta(weeks=interval)
                    elif unit == 'month':
                        month = current_due.month + interval
                        year = current_due.year
                        while month > 12:
                            month -= 12
                            year += 1
                        return current_due.replace(month=month, year=year)
                    elif unit == 'year':
                        return current_due.replace(year=current_due.year + interval)
                
            # If we can't parse the rule, just add a week
            return current_due + timedelta(weeks=1)
        except Exception as e:
            logger.error(f"Failed to calculate next due date: {e}")
            return None
    
    def _can_complete_task(self, task: Task, all_tasks: List[Task]) -> bool:
        """
        Check if a task can be completed (all dependencies are met).
        
        Args:
            task: Task to check
            all_tasks: List of all tasks
            
        Returns:
            bool: True if task can be completed, False otherwise
        """
        # Create a dictionary for faster lookup
        task_dict = {t.id: t for t in all_tasks}
        
        # Check each dependency
        for dep_id in task.dependencies:
            dep_task = task_dict.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
                
        return True
    
    def get_dependent_tasks(self, task_id: str) -> List[Task]:
        """
        Get tasks that depend on the specified task.
        
        Args:
            task_id: Task ID to find dependents for
            
        Returns:
            List[Task]: List of tasks that depend on the specified task
        """
        tasks = self._load_tasks()
        dependents = []
        
        for task in tasks:
            if task_id in task.dependencies:
                dependents.append(task)
                
        return dependents
    
    def get_blocked_tasks(self) -> List[Task]:
        """
        Get tasks that are blocked by uncompleted dependencies.
        
        Returns:
            List[Task]: List of blocked tasks
        """
        tasks = self._load_tasks()
        blocked = []
        
        for task in tasks:
            if task.status == TaskStatus.PENDING and not self._can_complete_task(task, tasks):
                blocked.append(task)
                
        return blocked
    
    def get_recurring_tasks(self) -> List[Task]:
        """
        Get all recurring task templates.
        
        Returns:
            List[Task]: List of recurring task templates
        """
        tasks = self._load_tasks()
        return [task for task in tasks if task.is_recurring and not task.recurring_task_id]
    
    def sync_with_google_tasks(self) -> bool:
        """
        Synchronize local tasks with Google Tasks.
        
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        if not self.use_google_tasks:
            logger.warning("Cannot sync with Google Tasks when not using Google Tasks mode")
            return False
        
        logger.info("Starting synchronization with Google Tasks")
        success = self.sync_manager.sync()
        if success:
            logger.info("Successfully synchronized with Google Tasks")
        else:
            logger.error("Failed to synchronize with Google Tasks")
        return success
    
    def _load_tasks(self):
        """Load tasks from local storage."""
        if self.use_google_tasks:
            # When using Google Tasks, we still use local storage as a cache
            pass
        
        task_dicts = self.storage.load_tasks()
        tasks = [Task(**task_dict) for task_dict in task_dicts]
        logger.debug(f"Loaded {len(tasks)} tasks from storage")
        return tasks
    
    def _save_tasks(self, tasks):
        """Save tasks to local storage."""
        # Always save to local storage as it acts as a cache/offline backup
        task_dicts = [task.model_dump() for task in tasks]
        self.storage.save_tasks(task_dicts)
        logger.debug(f"Saved {len(tasks)} tasks to storage")