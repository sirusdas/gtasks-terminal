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
            credentials_file: Path to credentials file
            token_file: Path to token file
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.auth_manager = GoogleAuthManager(credentials_file, token_file)
        self.service = None
        self.connected = False
        logger.debug("GoogleTasksClient initialized")
    
    def connect(self) -> bool:
        """
        Connect to the Google Tasks API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            credentials = self.auth_manager.authenticate()
            if not credentials:
                logger.error("Failed to authenticate with Google")
                return False
                
            from googleapiclient.discovery import build
            self.service = build('tasks', 'v1', credentials=credentials, cache_discovery=False)
            self.connected = True
            logger.info("Successfully connected to Google Tasks API")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Google Tasks API: {e}")
            return False
    
    def list_tasklists(self) -> List[Dict[str, Any]]:
        """
        List all task lists.
        
        Returns:
            List of task list dictionaries
        """
        if not self.service:
            logger.error("Google Tasks client not connected")
            return []
            
        try:
            tasklists_result = self.service.tasklists().list().execute()
            tasklists = tasklists_result.get('items', [])
            logger.debug(f"Found {len(tasklists)} task lists")
            return tasklists
        except HttpError as error:
            logger.error(f"Error listing task lists: {error}")
            return []
    
    def create_task(self, task_data):
        """
        Create a new task in Google Tasks.
        
        Args:
            task_data: Either a Task object or parameters for creating a task
            
        Returns:
            Task object if successful, None otherwise
        """
        if not self.service:
            logger.error("Google Tasks client not connected")
            return None
            
        # Handle both Task objects and individual parameters
        if hasattr(task_data, 'title'):  # It's a Task object
            title = task_data.title
            description = task_data.description
            due = task_data.due
            priority = task_data.priority
            project = task_data.project
            tags = task_data.tags
            tasklist_id = getattr(task_data, 'tasklist_id', '@default')
            notes = task_data.notes
            dependencies = task_data.dependencies
            recurrence_rule = task_data.recurrence_rule
        else:
            # It's individual parameters
            title = task_data
            description = None
            due = None
            priority = Priority.MEDIUM
            project = None
            tags = None
            tasklist_id = "@default"
            notes = None
            dependencies = None
            recurrence_rule = None

        # Import the deduplication utility here to avoid circular imports
        from gtasks_cli.utils.task_deduplication import is_task_duplicate
            
        # Check if task already exists to prevent duplicates
        if is_task_duplicate(
            title, 
            description or "", 
            str(due) if due else "", 
            "pending"
        ):
            logger.info(f"Task '{title}' already exists. Skipping creation.")
            return None

        try:
            # Prepare task data
            task_data = {
                'title': title
            }
            
            if description:
                task_data['notes'] = description
                
            if due:
                # Parse the due date
                if isinstance(due, str):
                    # Handle string dates
                    try:
                        due_date = datetime.fromisoformat(due.replace('Z', '+00:00'))
                    except ValueError:
                        # If parsing fails, try another format
                        due_date = datetime.fromisoformat(due)
                elif isinstance(due, datetime):
                    # Already a datetime object
                    due_date = due
                else:
                    # Some other type, convert to string first
                    due_date = datetime.fromisoformat(str(due).replace('Z', '+00:00'))
                    
                task_data['due'] = {
                    'dateTime': due_date.isoformat() + 'Z'
                }
            
            # Create the task in Google Tasks
            task_result = self.service.tasks().insert(
                tasklist=tasklist_id,
                body=task_data
            ).execute()
            
            # Convert to Task object
            task = Task(
                id=task_result['id'],
                title=task_result['title'],
                description=task_result.get('notes'),
                due=datetime.fromisoformat(task_result['due']['dateTime'].replace('Z', '+00:00')) if 'due' in task_result and 'dateTime' in task_result['due'] else None,
                priority=priority,
                status=TaskStatus.PENDING,
                project=project,
                tags=tags or [],
                notes=notes,
                dependencies=dependencies or [],
                recurrence_rule=recurrence_rule,
                created_at=datetime.fromisoformat(task_result['updated'].replace('Z', '+00:00')) if 'updated' in task_result else datetime.now(),
                modified_at=datetime.fromisoformat(task_result['updated'].replace('Z', '+00:00')) if 'updated' in task_result else datetime.now()
            )
            
            logger.info(f"Created task in Google Tasks: {task.title}")
            return task
            
        except Exception as e:
            logger.error(f"Error creating task in Google Tasks: {e}")
            return None
    
    def list_tasks(self, tasklist_id: str = "@default", 
                  show_completed: bool = False,
                  show_hidden: bool = False,
                  show_deleted: bool = False) -> List[Task]:
        """
        List tasks from a task list.
        
        Args:
            tasklist_id: The ID of the task list to retrieve tasks from
            show_completed: Whether to include completed tasks
            show_hidden: Whether to include hidden tasks
            show_deleted: Whether to include deleted tasks
            
        Returns:
            List of Task objects
        """
        if not self.service:
            logger.error("Google Tasks client not connected")
            return []
        
        try:
            tasks = []
            page_token = None
            
            # Loop through all pages of results
            while True:
                # Prepare the request with page token if available
                # Set maxResults to 100 (maximum allowed) to reduce number of requests
                request = self.service.tasks().list(
                    tasklist=tasklist_id,
                    pageToken=page_token,
                    maxResults=100,  # Maximum allowed by Google Tasks API
                    showCompleted=show_completed,
                    showHidden=show_hidden,
                    showDeleted=show_deleted
                )
                
                result = request.execute()
                google_tasks = result.get('items', [])
                logger.debug(f"Retrieved {len(google_tasks)} tasks from Google Tasks (page)")
                
                # Convert Google tasks to local tasks
                for google_task in google_tasks:
                    task = self._convert_google_task_to_local(google_task)
                    if task:
                        tasks.append(task)
                
                # Check if there are more pages
                page_token = result.get('nextPageToken')
                if not page_token:
                    break
            
            logger.debug(f"Retrieved total of {len(tasks)} tasks from Google Tasks")
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