"""
Google Tasks API client for the Google Tasks CLI application.
"""

from typing import List, Optional, Dict, Any
from googleapiclient.errors import HttpError
from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.integrations.google_auth import GoogleAuthManager
from gtasks_cli.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class GoogleTasksClient:
    """Client for interacting with the Google Tasks API."""
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        """
        Initialize the GoogleTasksClient.
        
        Args:
            credentials_file: Path to the client credentials JSON file
            token_file: Path to the token pickle file
        """
        self.auth_manager = GoogleAuthManager(credentials_file, token_file)
        self.service = None
    
    def connect(self) -> bool:
        """
        Connect to the Google Tasks API.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            self.service = self.auth_manager.get_service()
            if self.service:
                logger.info("Successfully connected to Google Tasks API")
                return True
            else:
                logger.error("Failed to connect to Google Tasks API")
                return False
        except Exception as e:
            logger.error(f"Connection to Google Tasks API failed: {e}")
            return False
    
    def list_tasklists(self) -> List[Dict[str, Any]]:
        """
        List all task lists.
        
        Returns:
            List[Dict[str, Any]]: List of task lists
        """
        if not self.service:
            if not self.connect():
                return []
        
        try:
            result = self.service.tasklists().list().execute()
            tasklists = result.get('items', [])
            logger.debug(f"Retrieved {len(tasklists)} tasklists")
            return tasklists
        except HttpError as e:
            logger.error(f"Failed to list tasklists: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing tasklists: {e}")
            return []
    
    def get_default_tasklist(self) -> Optional[Dict[str, Any]]:
        """
        Get the default task list (@default).
        
        Returns:
            Dict[str, Any]: The default task list, or None if not found
        """
        tasklists = self.list_tasklists()
        for tasklist in tasklists:
            if tasklist.get('id') == '@default':
                return tasklist
        return None
    
    def list_tasks(self, tasklist_id: str = '@default') -> List[Task]:
        """
        List tasks from a task list.
        
        Args:
            tasklist_id: The ID of the task list to retrieve tasks from
            
        Returns:
            List[Task]: List of tasks
        """
        if not self.service:
            if not self.connect():
                return []
        
        try:
            result = self.service.tasks().list(tasklist=tasklist_id).execute()
            google_tasks = result.get('items', [])
            logger.debug(f"Retrieved {len(google_tasks)} tasks from Google Tasks")
            
            tasks = []
            for google_task in google_tasks:
                task = self._convert_google_task_to_local(google_task)
                if task:
                    tasks.append(task)
            
            return tasks
        except HttpError as e:
            logger.error(f"Failed to list tasks: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing tasks: {e}")
            return []
    
    def get_task(self, task_id: str, tasklist_id: str = '@default') -> Optional[Task]:
        """
        Get a single task by ID.
        
        Args:
            task_id: The ID of the task to retrieve
            tasklist_id: The ID of the task list containing the task
            
        Returns:
            Task: The task, or None if not found
        """
        if not self.service:
            if not self.connect():
                return None
        
        try:
            result = self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
            logger.debug(f"Retrieved task {task_id} from Google Tasks")
            
            task = self._convert_google_task_to_local(result)
            return task
        except HttpError as e:
            if e.resp.status == 404:
                logger.debug(f"Task {task_id} not found in Google Tasks")
            else:
                logger.error(f"Failed to get task {task_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting task {task_id}: {e}")
            return None
    
    def create_task(self, task: Task, tasklist_id: str = '@default') -> Optional[Task]:
        """
        Create a task in Google Tasks.
        
        Args:
            task: The task to create
            tasklist_id: The ID of the task list to create the task in
            
        Returns:
            Task: The created task, or None if creation failed
        """
        if not self.service:
            if not self.connect():
                return None
        
        try:
            google_task = self._convert_local_task_to_google(task)
            result = self.service.tasks().insert(tasklist=tasklist_id, body=google_task).execute()
            logger.info(f"Created task in Google Tasks: {result.get('id')}")
            
            # Convert back to local task format
            created_task = self._convert_google_task_to_local(result)
            return created_task
        except HttpError as e:
            logger.error(f"Failed to create task: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating task: {e}")
            return None
    
    def update_task(self, task: Task, tasklist_id: str = '@default') -> Optional[Task]:
        """
        Update a task in Google Tasks.
        
        Args:
            task: The task to update
            tasklist_id: The ID of the task list containing the task
            
        Returns:
            Task: The updated task, or None if update failed
        """
        if not self.service:
            if not self.connect():
                return None
        
        try:
            google_task = self._convert_local_task_to_google(task)
            result = self.service.tasks().update(
                tasklist=tasklist_id, 
                task=task.id, 
                body=google_task
            ).execute()
            logger.info(f"Updated task in Google Tasks: {task.id}")
            
            # Convert back to local task format
            updated_task = self._convert_google_task_to_local(result)
            return updated_task
        except HttpError as e:
            logger.error(f"Failed to update task: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating task: {e}")
            return None
    
    def delete_task(self, task_id: str, tasklist_id: str = '@default') -> bool:
        """
        Delete a task from Google Tasks.
        
        Args:
            task_id: The ID of the task to delete
            tasklist_id: The ID of the task list containing the task
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.service:
            if not self.connect():
                return False
        
        try:
            self.service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
            logger.info(f"Deleted task from Google Tasks: {task_id}")
            return True
        except HttpError as e:
            logger.error(f"Failed to delete task: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting task: {e}")
            return False
    
    def complete_task(self, task_id: str, tasklist_id: str = '@default') -> bool:
        """
        Mark a task as completed in Google Tasks.
        
        Args:
            task_id: The ID of the task to complete
            tasklist_id: The ID of the task list containing the task
            
        Returns:
            bool: True if completion was successful, False otherwise
        """
        if not self.service:
            if not self.connect():
                return False
        
        try:
            # Get the task first
            task_result = self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
            
            # Update the task status to completed
            task_result['status'] = 'completed'
            if 'completed' not in task_result:
                task_result['completed'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            # Update the task
            self.service.tasks().update(
                tasklist=tasklist_id, 
                task=task_id, 
                body=task_result
            ).execute()
            
            logger.info(f"Completed task in Google Tasks: {task_id}")
            return True
        except HttpError as e:
            logger.error(f"Failed to complete task: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error completing task: {e}")
            return False
    
    def _convert_local_task_to_google(self, task: Task) -> Dict[str, Any]:
        """
        Convert a local task to Google Tasks format.
        
        Args:
            task: The local task to convert
            
        Returns:
            Dict[str, Any]: The Google Tasks formatted task
        """
        google_task = {
            'id': task.id,
            'title': task.title,
            'status': 'completed' if task.status == TaskStatus.COMPLETED else 
                     'needsAction' if task.status != TaskStatus.DELETED else 'needsAction',
        }
        
        if task.notes:
            google_task['notes'] = task.notes
            
        if task.due:
            if isinstance(task.due, datetime):
                google_task['due'] = task.due.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            else:
                google_task['due'] = str(task.due)
        
        # Handle deleted tasks
        if task.status == TaskStatus.DELETED:
            google_task['deleted'] = True
            
        return google_task
    
    def _convert_google_task_to_local(self, google_task: Dict[str, Any]) -> Optional[Task]:
        """
        Convert a Google Tasks task to local format.
        
        Args:
            google_task: The Google Tasks task to convert
            
        Returns:
            Task: The local formatted task, or None if conversion failed
        """
        try:
            # Handle deleted tasks
            if google_task.get('deleted', False):
                status = TaskStatus.DELETED
            elif google_task.get('status') == 'completed':
                status = TaskStatus.COMPLETED
            else:
                status = TaskStatus.PENDING
            
            # Parse due date
            due_date = None
            if 'due' in google_task and google_task['due']:
                try:
                    due_date = datetime.fromisoformat(google_task['due'].replace('Z', '+00:00'))
                except ValueError:
                    # Try alternative format
                    try:
                        due_date = datetime.strptime(google_task['due'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    except ValueError:
                        logger.warning(f"Failed to parse due date: {google_task['due']}")
            
            # Parse completed date
            completed_at = None
            if 'completed' in google_task and google_task['completed']:
                try:
                    completed_at = datetime.fromisoformat(google_task['completed'].replace('Z', '+00:00'))
                except ValueError:
                    try:
                        completed_at = datetime.strptime(google_task['completed'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    except ValueError:
                        logger.warning(f"Failed to parse completed date: {google_task['completed']}")
            
            # Parse created date
            created_at = datetime.utcnow()
            if 'updated' in google_task:
                try:
                    created_at = datetime.fromisoformat(google_task['updated'].replace('Z', '+00:00'))
                except ValueError:
                    try:
                        created_at = datetime.strptime(google_task['updated'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    except ValueError:
                        pass
            
            # Create the local task
            local_task = Task(
                id=google_task['id'],
                title=google_task['title'],
                notes=google_task.get('notes'),
                due=due_date,
                status=status,
                priority=Priority.MEDIUM,  # Google Tasks doesn't have priority
                project=None,  # Google Tasks doesn't have projects
                tags=[],  # Google Tasks doesn't have tags
                tasklist_id='@default',  # Default tasklist
                created_at=created_at,
                modified_at=created_at,
                completed_at=completed_at
            )
            
            return local_task
        except Exception as e:
            logger.error(f"Failed to convert Google task to local format: {e}")
            return None