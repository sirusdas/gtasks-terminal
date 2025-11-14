#!/usr/bin/env python3
"""
Sync Manager - Handles synchronization between local tasks and Google Tasks
"""

import json
import os
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task
from gtasks_cli.storage.local_storage import LocalStorage
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.utils.task_deduplication import create_task_signature, get_existing_task_signatures
from gtasks_cli.utils.datetime_utils import _normalize_datetime

logger = setup_logger(__name__)


class SyncManager:
    """Manages synchronization between local tasks and Google Tasks with conflict resolution."""
    
    def __init__(self, storage, google_client):
        """
        Initialize the SyncManager.
        
        Args:
            storage: An instance of a storage backend (e.g., LocalStorage, SQLiteStorage)
            google_client: An instance of GoogleTasksClient
        """
        self.local_storage = storage
        self.google_client = google_client
        self.sync_metadata_file = os.path.join(
            os.path.expanduser("~"), ".gtasks", "sync_metadata.json"
        )
        self.deletion_log_file = os.path.join(
            os.path.expanduser("~"), ".gtasks", "deletion_log.json"
        )
        self.sync_metadata = self._load_sync_metadata()
    
    def _load_sync_metadata(self) -> Dict:
        """
        Load synchronization metadata.
        
        Returns:
            Dict: Sync metadata
        """
        if os.path.exists(self.sync_metadata_file):
            try:
                with open(self.sync_metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sync metadata: {e}")
        
        # Return default metadata structure
        return {
            "last_sync": None,
            "local_task_versions": {},
            "google_task_versions": {},
            "task_mappings": {},  # Maps local task IDs to Google task IDs
            "conflicts": [],
            "sync_log": []  # Log of sync operations
        }
    
    def _save_sync_metadata(self):
        """Save synchronization metadata."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.sync_metadata_file), exist_ok=True)
            
            with open(self.sync_metadata_file, 'w') as f:
                json.dump(self.sync_metadata, f, indent=2, default=str)
            logger.debug("Sync metadata saved successfully")
        except Exception as e:
            logger.error(f"Failed to save sync metadata: {e}")
    
    def _log_deletion(self, task: Task, reason: str):
        """
        Log task deletion to a deletion log file.
        
        Args:
            task: The task that was deleted
            reason: Reason for deletion
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.deletion_log_file), exist_ok=True)
            
            # Load existing deletion log
            deletion_log = []
            if os.path.exists(self.deletion_log_file):
                with open(self.deletion_log_file, 'r') as f:
                    try:
                        deletion_log = json.load(f)
                    except json.JSONDecodeError:
                        deletion_log = []
            
            # Add new deletion entry
            deletion_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "task_id": task.id,
                "task_title": task.title,
                "task_description": task.description,
                "task_due": task.due.isoformat() if task.due else None,
                "task_status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                "reason": reason
            }
            
            deletion_log.append(deletion_entry)
            
            # Save updated deletion log
            with open(self.deletion_log_file, 'w') as f:
                json.dump(deletion_log, f, indent=2, default=str)
                
            logger.info(f"Logged deletion of task '{task.title}' (ID: {task.id}) - Reason: {reason}")
        except Exception as e:
            logger.error(f"Failed to log deletion: {e}")
    
    def sync(self) -> bool:
        """
        Synchronize local tasks with Google Tasks following the specified sync logic.
        
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        logger.info("Starting synchronization process")
        
        # Connect to Google Tasks
        if not self.google_client.connect():
            logger.error("Failed to connect to Google Tasks")
            return False
        
        try:
            # Load local tasks
            local_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
            logger.debug(f"Loaded {len(local_tasks)} local tasks")
            
            # Load list mappings for local tasks
            list_mappings = self.local_storage.load_list_mapping()
            
            # Load all Google Tasks from all lists
            all_google_tasks = []
            tasklists = self.google_client.list_tasklists()
            
            # Create a mapping of tasklist titles to IDs
            tasklist_title_to_id = {tasklist['title']: tasklist['id'] for tasklist in tasklists}
            
            for tasklist in tasklists:
                tasklist_id = tasklist['id']
                google_tasks = self.google_client.list_tasks(
                    tasklist_id=tasklist_id,
                    show_completed=True,
                    show_hidden=True,
                    show_deleted=False
                )
                # Add tasklist information to each task
                for task in google_tasks:
                    task.tasklist_id = tasklist_id
                all_google_tasks.extend(google_tasks)
                logger.debug(f"Loaded {len(google_tasks)} Google tasks from '{tasklist['title']}'")
            
            logger.debug(f"Loaded total of {len(all_google_tasks)} Google tasks from all lists")
            
            # First, remove duplicates from Google Tasks
            self._remove_google_duplicates(all_google_tasks, tasklists)
            
            # Reload Google Tasks after deduplication
            all_google_tasks = []
            for tasklist in tasklists:
                tasklist_id = tasklist['id']
                google_tasks = self.google_client.list_tasks(
                    tasklist_id=tasklist_id,
                    show_completed=True,
                    show_hidden=True,
                    show_deleted=False
                )
                # Add tasklist information to each task
                for task in google_tasks:
                    task.tasklist_id = tasklist_id
                all_google_tasks.extend(google_tasks)
            
            # Get existing task signatures to prevent duplicates
            existing_signatures = get_existing_task_signatures(use_google_tasks=True)
            
            # Perform synchronization following the specified logic
            synced_tasks = self._perform_sync(local_tasks, all_google_tasks, list_mappings, tasklist_title_to_id, existing_signatures)
            
            # Save synchronized tasks locally
            task_dicts = [task.model_dump() for task in synced_tasks]
            self.local_storage.save_tasks(task_dicts)

            # Create and save the list mapping
            new_list_mapping = {}
            tasklist_id_to_title = {tl['id']: tl.get('title', 'Unknown List') for tl in tasklists}
            for task in synced_tasks:
                if task.tasklist_id in tasklist_id_to_title:
                    new_list_mapping[task.id] = tasklist_id_to_title[task.tasklist_id]
            self.local_storage.save_list_mapping(new_list_mapping)
            
            # Update sync metadata
            self.sync_metadata["last_sync"] = datetime.utcnow().isoformat()
            self._save_sync_metadata()
            
            logger.info("Synchronization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _remove_google_duplicates(self, google_tasks: List[Task], tasklists: List[Dict]):
        """
        Remove duplicate tasks from Google Tasks.
        
        Args:
            google_tasks: List of all Google tasks
            tasklists: List of task lists
        """
        # Group tasks by signature to identify duplicates
        tasks_by_signature = {}
        
        for task in google_tasks:
            # Create signature for task comparison
            signature = create_task_signature(
                task.title or "",
                task.description or "",
                task.due,
                task.status if hasattr(task, 'status') else None
            )
            
            if signature not in tasks_by_signature:
                tasks_by_signature[signature] = []
            tasks_by_signature[signature].append(task)
        
        # Remove duplicates, keeping only one instance of each task
        duplicates_removed = 0
        for signature, tasks in tasks_by_signature.items():
            if len(tasks) > 1:
                # Sort tasks by modification time, keep the most recently modified one
                tasks.sort(key=lambda x: _normalize_datetime(x.modified_at) or _normalize_datetime(datetime.min), reverse=True)
                
                # Remove all but the most recent task
                for task in tasks[1:]:
                    try:
                        self.google_client.delete_task(task.id, task.tasklist_id)
                        duplicates_removed += 1
                        logger.info(f"Removed duplicate task: {task.title} (ID: {task.id})")
                    except Exception as e:
                        logger.error(f"Failed to remove duplicate task {task.id}: {e}")
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate tasks from Google Tasks")
    
    def _perform_sync(self, local_tasks: List[Task], google_tasks: List[Task], 
                      list_mappings: Dict[str, str], tasklist_title_to_id: Dict[str, str],
                      existing_signatures: set) -> List[Task]:
        """
        Perform synchronization between local and Google tasks.
        
        Args:
            local_tasks: List of local tasks
            google_tasks: List of Google tasks
            list_mappings: Mapping of local task IDs to list names
            tasklist_title_to_id: Mapping of tasklist titles to IDs
            existing_signatures: Set of existing task signatures to prevent duplicates
            
        Returns:
            List[Task]: List of synchronized tasks
        """
        # Create mappings for easier lookup
        local_task_dict = {task.id: task for task in local_tasks}
        google_task_dict = {task.id: task for task in google_tasks}
        
        # Create signature-based mappings
        local_signature_to_task = {}
        google_signature_to_task = {}
        
        for task in local_tasks:
            signature = create_task_signature(
                title=task.title or "",
                description=task.description or "",
                due_date=task.due,
                status=task.status
            )
            local_signature_to_task[signature] = task
        
        for task in google_tasks:
            signature = create_task_signature(
                title=task.title or "",
                description=task.description or "",
                due_date=task.due,
                status=task.status
            )
            google_signature_to_task[signature] = task
        
        # Synchronize tasks
        synced_tasks = []
        
        # Process local tasks - upload new or updated tasks to Google
        for local_task in local_tasks:
            local_signature = create_task_signature(
                title=local_task.title or "",
                description=local_task.description or "",
                due_date=local_task.due,
                status=local_task.status
            )
            
            # Determine which tasklist this task should be in
            tasklist_name = list_mappings.get(local_task.id, "My Tasks")
            tasklist_id = tasklist_title_to_id.get(tasklist_name)
            
            # If tasklist doesn't exist, use default
            if not tasklist_id:
                tasklist_id = "@default"
            
            # Check if this task exists in Google Tasks
            if local_task.id in google_task_dict:
                # Task exists in Google, check if it needs updating
                google_task = google_task_dict[local_task.id]
                
                # Update the task in Google if it has changed
                local_modified = _normalize_datetime(local_task.modified_at) or _normalize_datetime(datetime.min)
                google_modified = _normalize_datetime(google_task.modified_at) or _normalize_datetime(datetime.min)
                
                if local_modified > google_modified:
                    # Update task in Google
                    updated_task = self.google_client.update_task(local_task, tasklist_id)
                    if updated_task:
                        synced_tasks.append(updated_task)
                        logger.debug(f"Updated task in Google: {local_task.title}")
                    else:
                        synced_tasks.append(google_task)  # Keep the Google version if update failed
                else:
                    # Keep the Google version
                    synced_tasks.append(google_task)
            else:
                # Task doesn't exist in Google, check by signature
                if local_signature in google_signature_to_task:
                    # Task exists in Google with different ID, update it
                    google_task = google_signature_to_task[local_signature]
                    # Update the local task ID to match Google
                    local_task.id = google_task.id
                    # Update task in Google
                    updated_task = self.google_client.update_task(local_task, google_task.tasklist_id)
                    if updated_task:
                        synced_tasks.append(updated_task)
                        logger.debug(f"Updated task in Google (ID sync): {local_task.title}")
                    else:
                        synced_tasks.append(google_task)
                else:
                    # Completely new task, create it in Google
                    # Set the tasklist_id for the new task
                    local_task.tasklist_id = tasklist_id
                    
                    # Check if this task already exists to prevent duplicates
                    task_signature = create_task_signature(
                        title=local_task.title or "",
                        description=local_task.description or "",
                        due_date=local_task.due,
                        status=local_task.status
                    )
                    
                    if task_signature in existing_signatures:
                        logger.info(f"Task '{local_task.title}' already exists in Google Tasks. Skipping creation.")
                        # Find the existing task and add it to synced tasks
                        for google_task in google_tasks:
                            google_signature = create_task_signature(
                                title=google_task.title or "",
                                description=google_task.description or "",
                                due_date=google_task.due,
                                status=google_task.status
                            )
                            if google_signature == task_signature:
                                synced_tasks.append(google_task)
                                break
                    else:
                        new_task = self.google_client.create_task(local_task)
                        if new_task:
                            synced_tasks.append(new_task)
                            logger.debug(f"Created new task in Google: {local_task.title}")
                        else:
                            synced_tasks.append(local_task)  # Keep local version if creation failed
        
        # Process Google tasks - download new tasks from Google
        for google_task in google_tasks:
            google_signature = create_task_signature(
                title=google_task.title or "",
                description=google_task.description or "",
                due_date=google_task.due,
                status=google_task.status
            )
            
            if google_task.id not in local_task_dict and google_signature not in local_signature_to_task:
                # This is a new task from Google, add it to local tasks
                synced_tasks.append(google_task)
                logger.debug(f"Downloaded new task from Google: {google_task.title}")
        
        logger.info(f"Synchronized {len(synced_tasks)} tasks")
        return synced_tasks
    
    def is_connected(self) -> bool:
        """
        Check if connected to Google Tasks.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.google_client.connect()
    
    def get_offline_tasks(self) -> List[Task]:
        """
        Get tasks from local storage for offline access.
        
        Returns:
            List[Task]: List of tasks from local storage
        """
        task_dicts = self.local_storage.load_tasks()
        return [Task(**task_dict) for task_dict in task_dicts]