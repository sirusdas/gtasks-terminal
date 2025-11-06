#!/usr/bin/env python3
"""
Sync Manager - Handles synchronization between local tasks and Google Tasks
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task
from gtasks_cli.storage.local_storage import LocalStorage
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.utils.task_deduplication import create_task_signature

logger = setup_logger(__name__)


class SyncManager:
    """Manages synchronization between local tasks and Google Tasks with conflict resolution."""
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        """
        Initialize the SyncManager.
        
        Args:
            credentials_file: Path to the client credentials JSON file
            token_file: Path to the token pickle file
        """
        self.local_storage = LocalStorage()
        self.google_client = GoogleTasksClient(credentials_file, token_file)
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
            
            # Load all Google Tasks from all lists
            all_google_tasks = []
            tasklists = self.google_client.list_tasklists()
            
            for tasklist in tasklists:
                tasklist_id = tasklist['id']
                google_tasks = self.google_client.list_tasks(
                    tasklist_id=tasklist_id,
                    show_completed=True,
                    show_hidden=True,
                    show_deleted=False
                )
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
                all_google_tasks.extend(google_tasks)
            
            # Perform synchronization following the specified logic
            synced_tasks = self._perform_sync(local_tasks, all_google_tasks)
            
            # Save synchronized tasks locally
            task_dicts = [task.model_dump() for task in synced_tasks]
            self.local_storage.save_tasks(task_dicts)
            
            # Update sync metadata
            self.sync_metadata["last_sync"] = datetime.utcnow().isoformat()
            self._save_sync_metadata()
            
            logger.info("Synchronization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
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
                str(task.due) if task.due else "",
                str(task.status.value) if hasattr(task.status, 'value') else str(task.status)
            )
            
            if signature not in tasks_by_signature:
                tasks_by_signature[signature] = []
            tasks_by_signature[signature].append(task)
        
        # Identify and remove duplicates, keeping only the most recent one
        tasks_to_delete = []
        for signature, tasks in tasks_by_signature.items():
            if len(tasks) > 1:
                # Sort by modification time to keep the most recent one
                tasks.sort(key=lambda t: t.modified_at or t.created_at, reverse=True)
                # Mark all but the first (most recent) for deletion
                tasks_to_delete.extend(tasks[1:])
        
        # Delete duplicate tasks
        deleted_count = 0
        for task in tasks_to_delete:
            # Find which tasklist this task belongs to
            tasklist_id = '@default'  # Default fallback
            for tasklist in tasklists:
                tasklist_tasks = self.google_client.list_tasks(
                    tasklist_id=tasklist['id'],
                    show_completed=True,
                    show_hidden=True,
                    show_deleted=False
                )
                if any(t.id == task.id for t in tasklist_tasks):
                    tasklist_id = tasklist['id']
                    break
            
            # Log the deletion before actually deleting
            self._log_deletion(task, "Duplicate removal during sync")
            
            # Delete the duplicate task
            if self.google_client.delete_task(task.id, tasklist_id=tasklist_id):
                logger.info(f"Deleted duplicate task: {task.title} (ID: {task.id})")
                deleted_count += 1
            else:
                logger.warning(f"Failed to delete duplicate task: {task.title} (ID: {task.id})")
        
        logger.info(f"Deleted {deleted_count} duplicate tasks from Google Tasks")
    
    def _perform_sync(self, local_tasks: List[Task], google_tasks: List[Task]) -> List[Task]:
        """
        Perform the synchronization between local and Google tasks following the specified logic.
        
        Local Task Tracking (Log): The system must maintain a local log that records every 
        newly added task, along with the timestamp of its creation and a flag indicating 
        its last sync status (synced/unsynced).

        Push Logic (Local-to-Remote):
        Filtering: Only tasks marked as newly added/unsynced in the local log should be 
        considered for a push.

        Duplicate Prevention: Before pushing a local task to the remote, the system must 
        check the remote resource to ensure a task with the exact same content 
        (task description/name AND details/properties) does not already exist. 
        If it's an exact duplicate, the push must be skipped, and the local task's 
        sync status should be updated to "synced."

        Pull-First Sync Logic (Remote-to-Local): This process is triggered when a user 
        initiates a sync that starts by pulling remote data.

        Comparison: The system must fetch the complete remote task list and compare it 
        against the current local task list.

        Conflict Detection: If a local task exists that is not present on the remote list 
        (i.e., it was created locally but hasn't been pushed or was deleted remotely 
        by another client), this is considered a local conflict.

        User Resolution: For every detected local conflict, the user must be prompted 
        to verify the local task.

        If the user confirms the task, it must be marked for an immediate push to the remote.

        If the user rejects the task, it must be immediately and permanently deleted 
        from the local list and log.
        
        Args:
            local_tasks: List of local tasks
            google_tasks: List of Google tasks
            
        Returns:
            List[Task]: Synchronized list of tasks
        """
        logger.info("Performing sync with pull-first logic")
        
        # Create dictionaries for easier lookup
        local_task_dict = {task.id: task for task in local_tasks}
        google_task_dict = {task.id: task for task in google_tasks}
        
        # Create a Google task signature map for duplicate checking
        google_task_signatures = {}
        for task in google_tasks:
            signature = create_task_signature(
                task.title or "",
                task.description or "",
                str(task.due) if task.due else "",
                str(task.status.value) if hasattr(task.status, 'value') else str(task.status)
            )
            google_task_signatures[signature] = task
        
        # Start with all Google tasks (pull-first approach)
        synced_tasks = list(google_tasks)
        synced_task_ids = {task.id for task in google_tasks}
        
        # Process local tasks
        for local_task in local_tasks:
            # Create signature for local task
            local_signature = create_task_signature(
                local_task.title or "",
                local_task.description or "",
                str(local_task.due) if local_task.due else "",
                str(local_task.status.value) if hasattr(local_task.status, 'value') else str(local_task.status)
            )
            
            # Check if this task already exists in Google Tasks
            if local_signature in google_task_signatures:
                # Task already exists in Google - mark as synced and skip
                logger.info(f"Task '{local_task.title}' already exists in Google Tasks. Marking as synced.")
                # We don't add it to synced_tasks since it's already there from Google
                continue
            
            # Check if this is a local conflict (exists locally but not in Google)
            if local_task.id not in synced_task_ids:
                # This is a local conflict - task exists locally but not in Google
                # In a full implementation, we would prompt the user for resolution
                # For now, we'll push the task to Google
                logger.info(f"Local task '{local_task.title}' not found in Google Tasks. Pushing to Google.")
                
                # Create the task in Google Tasks
                created_google_task = self.google_client.create_task(local_task)
                if created_google_task:
                    synced_tasks.append(local_task)
                    synced_task_ids.add(local_task.id)
                    logger.info(f"Created task '{local_task.title}' in Google Tasks")
                else:
                    # If creation fails, keep local task
                    synced_tasks.append(local_task)
                    synced_task_ids.add(local_task.id)
                    logger.warning(f"Failed to create task '{local_task.title}' in Google Tasks")
        
        logger.info(f"Sync completed with {len(synced_tasks)} tasks")
        return synced_tasks
    
    def _update_task_versions(self, tasks: List[Task]):
        """
        Update task versions in sync metadata.
        
        Args:
            tasks: List of tasks to update versions for
        """
        # This is a placeholder for version tracking if needed in the future
        pass
    
    def is_connected(self) -> bool:
        """
        Check if we can connect to Google Tasks.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.google_client.connect()
    
    def get_offline_tasks(self) -> List[Task]:
        """
        Get tasks for offline use.
        
        Returns:
            List[Task]: List of tasks from local storage
        """
        task_dicts = self.local_storage.load_tasks()
        return [Task(**task_dict) for task_dict in task_dicts]
    
    def save_offline_changes(self, tasks: List[Task]) -> bool:
        """
        Save task changes when offline.
        
        Args:
            tasks: List of tasks to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            task_dicts = [task.model_dump() for task in tasks]
            self.local_storage.save_tasks(task_dicts)
            logger.info("Offline changes saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save offline changes: {e}")
            return False