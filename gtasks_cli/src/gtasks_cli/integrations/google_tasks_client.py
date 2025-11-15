import os
import pickle
import traceback
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.utils.task_deduplication import is_task_duplicate, create_task_signature
from gtasks_cli.integrations.google_auth import GoogleAuthManager

logger = setup_logger(__name__)


class GoogleTasksClient:
    """Client for interacting with the Google Tasks API."""
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        """
        Initialize the Google Tasks client.
        
        Args:
            credentials_file: Path to the credentials file
            token_file: Path to the token file
        """
        self.auth_manager = GoogleAuthManager(credentials_file, token_file)
        self.service = None
        self._default_tasklist_id = None
        self._auth_failed = False  # Track authentication failures
        logger.debug(f"GoogleTasksClient initialized with credentials: {credentials_file}, token: {token_file}")
    
    def connect(self) -> bool:
        """
        Connect to the Google Tasks API.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        # If we've already failed authentication, don't try again unless we're explicitly resetting
        if self._auth_failed:
            logger.error("Authentication previously failed. Not attempting to reconnect to prevent duplicates.")
            return False
            
        try:
            self.service = self.auth_manager.get_service()
            
            if not self.service:
                logger.error("Failed to get Google Tasks API service")
                self._auth_failed = True  # Mark authentication as failed
                return False
            
            # Get the default task list ID
            tasklists = self.service.tasklists().list().execute()
            for tasklist in tasklists.get('items', []):
                if tasklist.get('kind') == 'tasks#taskList' and tasklist.get('title') == 'My Tasks':
                    self._default_tasklist_id = tasklist['id']
            
            # If "My Tasks" list not found, use the first available list
            if not self._default_tasklist_id and tasklists.get('items'):
                self._default_tasklist_id = tasklists['items'][0]['id']
            
            # If no lists found, use a default ID
            if not self._default_tasklist_id:
                self._default_tasklist_id = "@default"
            
            logger.debug(f"Using tasklist ID: {self._default_tasklist_id}")
            # Reset the auth failed flag on successful connection
            self._auth_failed = False
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Tasks API: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._auth_failed = True  # Mark authentication as failed
            return False
    
    def list_tasklists(self) -> List[Dict[str, Any]]:
        """
        List all task lists.
        
        Returns:
            List of task list dictionaries
        """
        # Connect if not already connected
        if not self.service:
            if not self.connect():
                logger.error("Failed to connect to Google Tasks API")
                return []
            
        try:
            tasklists_result = self.service.tasklists().list().execute()
            tasklists = tasklists_result.get('items', [])
            logger.debug(f"Found {len(tasklists)} task lists")
            return tasklists
        except HttpError as error:
            logger.error(f"Error listing task lists: {error}")
            return []
    
    def get_tasklist_title(self, tasklist_id: str) -> Optional[str]:
        """
        Get the title of a tasklist by its ID.
        
        Args:
            tasklist_id: The ID of the tasklist
            
        Returns:
            The title of the tasklist or None if not found
        """
        try:
            tasklist = self.service.tasklists().get(tasklist=tasklist_id).execute()
            return tasklist.get('title')
        except Exception as e:
            logger.error(f"Error getting tasklist title: {e}")
            return None

    def create_task(self, task_data, existing_signatures: Optional[Set[str]] = None):
        """
        Create a new task in Google Tasks.
        
        Args:
            task_data: Either a Task object or parameters for creating a task
            existing_signatures: Optional set of existing task signatures to avoid duplicates
            
        Returns:
            Task object if successful, None otherwise
        """
        # CRITICAL: Check if we can connect to Google Tasks before attempting to create a task
        if not self.service:
            if not self.connect():
                logger.error("CRITICAL: Failed to connect to Google Tasks. ABORTING task creation to prevent duplicates.")
                return None
        
        # CRITICAL: If authentication has failed previously, do not attempt to create tasks
        if self._auth_failed:
            logger.error("CRITICAL: Authentication has previously failed. ABORTING task creation to prevent duplicates.")
            return None
            
        # Handle both Task objects and individual parameters
        if hasattr(task_data, 'title'):  # It's a Task object
            title = task_data.title
            description = task_data.description
            due = task_data.due
            priority = task_data.priority
            project = task_data.project
            tags = task_data.tags
            tasklist_id = getattr(task_data, 'tasklist_id', None) or self._default_tasklist_id or "@default"
            notes = task_data.notes
            dependencies = task_data.dependencies
            recurrence_rule = task_data.recurrence_rule
        else:
            # It's individual parameters (dict)
            title = task_data.get('title')
            description = task_data.get('description')
            due = task_data.get('due')
            priority = task_data.get('priority', Priority.MEDIUM)
            project = task_data.get('project')
            tags = task_data.get('tags')
            tasklist_id = task_data.get('tasklist_id') or self._default_tasklist_id or "@default"
            notes = task_data.get('notes')
            dependencies = task_data.get('dependencies')
            recurrence_rule = task_data.get('recurrence_rule')
        
        logger.debug(f"Tasklist ID from task_data: {task_data.get('tasklist_id') if isinstance(task_data, dict) else getattr(task_data, 'tasklist_id', None)}")
        logger.debug(f"Default tasklist ID: {self._default_tasklist_id}")
        logger.debug(f"Final tasklist ID: {tasklist_id}")
        
        # Use create_task_signature to precompute signatures for better performance
        from gtasks_cli.utils.task_deduplication import is_task_duplicate, create_task_signature
            
        # Format the due date the same way it will be stored in Google Tasks
        formatted_due = None
        if due:
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
            
            # Format the due date correctly for Google Tasks API
            formatted_due = due_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            # Then parse it back to match how it will be stored
            formatted_due = str(datetime.fromisoformat(formatted_due.replace('Z', '+00:00')))
            
        # Check if task already exists to prevent duplicates
        logger.debug(f"Checking for duplicate task: title='{title}', description='{description}', due='{formatted_due}', status='pending'")
        
        # Create a signature for this task
        task_signature = create_task_signature(
            title=title,
            description=description or "",
            due_date=formatted_due or ""
        )
        
        # If we have existing signatures, check against them
        if existing_signatures:
            is_duplicate = task_signature in existing_signatures
        else:
            # Fall back to checking against Google Tasks if no existing signatures provided
            is_duplicate = is_task_duplicate(
                task_title=title, 
                task_description=description or "", 
                task_due_date=formatted_due or "", 
                task_status="pending",
                use_google_tasks=True
            )
        
        if is_duplicate:
            logger.info(f"Task '{title}' already exists. Skipping creation.")
            return None
        else:
            logger.debug(f"Task '{title}' is not a duplicate. Proceeding with creation.")
        
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
                
                # Format the due date correctly for Google Tasks API
                task_data['due'] = due_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            # CRITICAL: Check if we still have a valid connection before creating the task
            if not self.service:
                logger.error("CRITICAL: No valid connection to Google Tasks. ABORTING task creation to prevent duplicates.")
                return None
                
            # CRITICAL: If authentication has failed previously, do not attempt to create tasks
            if self._auth_failed:
                logger.error("CRITICAL: Authentication has previously failed. ABORTING task creation to prevent duplicates.")
                return None
            
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
                due=datetime.fromisoformat(task_result['due'].replace('Z', '+00:00')) if 'due' in task_result else None,
                priority=priority,
                status=TaskStatus.PENDING,
                project=project,
                tags=tags or [],
                notes=notes,
                dependencies=dependencies or [],
                recurrence_rule=recurrence_rule,
                created_at=datetime.fromisoformat(task_result['updated'].replace('Z', '+00:00')) if 'updated' in task_result else datetime.now(),
                modified_at=datetime.fromisoformat(task_result['updated'].replace('Z', '+00:00')) if 'updated' in task_result else datetime.now(),
                tasklist_id=self._default_tasklist_id or "@default"
            )
            
            logger.info(f"Created task in Google Tasks: {task.title}")
            return task
            
        except Exception as e:
            logger.error(f"Error creating task in Google Tasks: {e}")
            # Mark authentication as failed if we get an auth error
            if 'invalid_grant' in str(e):
                self._auth_failed = True
                logger.error("CRITICAL: Authentication failed during task creation. Marking auth as failed to prevent duplicates.")
            return None
    
    def list_tasks(self, tasklist_id: str = None, 
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
            if not self.connect():
                return []
        
        tasklist_id = tasklist_id or self._default_tasklist_id or "@default"
        
        try:
            # Build parameters for the request
            params = {
                'tasklist': tasklist_id,
                'showCompleted': show_completed,
                'showHidden': show_hidden,
                'showDeleted': show_deleted
            }
            
            tasks = []
            page_token = None
            
            # Handle pagination
            while True:
                # Add page token if we have one
                if page_token:
                    params['pageToken'] = page_token
                
                # Execute the request
                result = self.service.tasks().list(**params).execute()
                
                # Convert to Task objects
                for item in result.get('items', []):
                    task = self._convert_google_task_to_local(item)
                    task.tasklist_id = tasklist_id  # Set the tasklist_id
                    tasks.append(task)
                
                # Check if there are more pages
                page_token = result.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"Retrieved {len(tasks)} tasks from Google Tasks (tasklist: {tasklist_id})")
            return tasks
        except Exception as e:
            logger.error(f"Error listing tasks from Google Tasks: {e}")
            return []
    
    def get_task(self, task_id: str, tasklist_id: str = None) -> Optional[Task]:
        """
        Get a specific task by ID.
        
        Args:
            task_id: The ID of the task to retrieve
            tasklist_id: The ID of the task list containing the task
            
        Returns:
            Task object or None if not found
        """
        if not self.service:
            if not self.connect():
                return None
        
        tasklist_id = tasklist_id or self._default_tasklist_id or "@default"
        
        try:
            task_result = self.service.tasks().get(
                tasklist=tasklist_id,
                task=task_id
            ).execute()
            
            task = self._convert_google_task_to_local(task_result)
            task.tasklist_id = tasklist_id  # Set the tasklist_id
            return task
        except Exception as e:
            logger.error(f"Error getting task from Google Tasks: {e}")
            return None
    
    def update_task(self, task: Task, tasklist_id: str = None) -> Optional[Task]:
        """
        Update a task in Google Tasks.
        
        Args:
            task: The task to update
            tasklist_id: The ID of the task list containing the task
            
        Returns:
            Updated Task object or None if update failed
        """
        if not self.service:
            if not self.connect():
                return None
        
        tasklist_id = tasklist_id or task.tasklist_id or self._default_tasklist_id or "@default"
        
        try:
            # Convert local task to Google Tasks format
            google_task = self._convert_local_task_to_google(task)
            
            # Update the task in Google Tasks
            result = self.service.tasks().update(
                tasklist=tasklist_id,
                task=task.id,
                body=google_task
            ).execute()
            logger.info(f"Updated task in Google Tasks: {task.id}")
            
            # Convert back to local task format
            updated_task = self._convert_google_task_to_local(result)
            updated_task.tasklist_id = tasklist_id  # Set the tasklist_id
            return updated_task
        except HttpError as e:
            logger.error(f"Failed to update task: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating task: {e}")
            return None
    
    def delete_task(self, task_id: str, tasklist_id: str = None) -> bool:
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
        
        tasklist_id = tasklist_id or self._default_tasklist_id or "@default"
        
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
    
    def complete_task(self, task_id: str, tasklist_id: str = None) -> bool:
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
        
        tasklist_id = tasklist_id or self._default_tasklist_id or "@default"
        
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
            'title': task.title,
            'status': 'completed' if task.status == TaskStatus.COMPLETED else 'needsAction',
        }
        
        if task.id:
            google_task['id'] = task.id
            
        if task.description:
            google_task['notes'] = task.description
            
        if task.due:
            # Handle due dates properly
            if isinstance(task.due, datetime):
                google_task['due'] = task.due.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            else:
                # If it's a string, try to parse it
                try:
                    due_date = datetime.fromisoformat(str(task.due).replace('Z', '+00:00'))
                    google_task['due'] = due_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                except ValueError:
                    # If parsing fails, just use the string
                    google_task['due'] = str(task.due)
        
        if task.status == TaskStatus.COMPLETED and hasattr(task, 'completed_at') and task.completed_at:
            google_task['completed'] = task.completed_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
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