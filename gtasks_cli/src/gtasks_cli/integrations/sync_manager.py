"""
Sync manager for handling synchronization between local and Google Tasks with conflict resolution.
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task
from gtasks_cli.storage.local_storage import LocalStorage
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient

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
            "conflicts": []
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
    
    def sync(self) -> bool:
        """
        Synchronize local tasks with Google Tasks.
        
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
            
            # Load Google Tasks
            google_tasks = self.google_client.list_tasks()
            logger.debug(f"Loaded {len(google_tasks)} Google tasks")
            
            # Perform synchronization
            synced_tasks = self._perform_sync(local_tasks, google_tasks)
            
            # Save synchronized tasks locally
            task_dicts = [task.model_dump() for task in synced_tasks]
            self.local_storage.save_tasks(task_dicts)
            
            # Update sync metadata
            self.sync_metadata["last_sync"] = datetime.utcnow().isoformat()
            self._update_task_versions(synced_tasks)
            self._save_sync_metadata()
            
            logger.info("Synchronization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            return False
    
    def _perform_sync(self, local_tasks: List[Task], google_tasks: List[Task]) -> List[Task]:
        """
        Perform the actual synchronization between local and Google tasks.
        
        Args:
            local_tasks: List of local tasks
            google_tasks: List of Google tasks
            
        Returns:
            List[Task]: Synchronized list of tasks
        """
        # Create dictionaries for easier lookup
        local_task_dict = {task.id: task for task in local_tasks}
        google_task_dict = {task.id: task for task in google_tasks}
        
        # Get all unique task IDs
        all_task_ids = set(local_task_dict.keys()) | set(google_task_dict.keys())
        
        # Process each task
        synced_tasks = []
        conflicts = []
        
        for task_id in all_task_ids:
            local_task = local_task_dict.get(task_id)
            google_task = google_task_dict.get(task_id)
            
            # Resolve conflicts if both local and Google tasks exist and have been modified
            if local_task and google_task:
                conflict_resolution = self._resolve_conflict(local_task, google_task)
                if conflict_resolution == "local":
                    synced_tasks.append(local_task)
                elif conflict_resolution == "google":
                    synced_tasks.append(google_task)
                elif conflict_resolution == "merge":
                    # For now, we'll use the local task as the merged result
                    # In a more advanced implementation, we could actually merge the fields
                    merged_task = self._merge_tasks(local_task, google_task)
                    synced_tasks.append(merged_task)
            elif local_task:
                # Only exists locally, push to Google
                if self.google_client.create_task(local_task):
                    synced_tasks.append(local_task)
                else:
                    # If push fails, keep local task
                    synced_tasks.append(local_task)
            elif google_task:
                # Only exists in Google, pull to local
                synced_tasks.append(google_task)
        
        # Handle conflicts that need user input
        if conflicts:
            self.sync_metadata["conflicts"].extend(conflicts)
            logger.info(f"Found {len(conflicts)} conflicts requiring user resolution")
        
        return synced_tasks
    
    def _resolve_conflict(self, local_task: Task, google_task: Task) -> str:
        """
        Resolve conflict between local and Google task versions.
        
        Args:
            local_task: Local task
            google_task: Google task
            
        Returns:
            str: Resolution strategy ("local", "google", or "merge")
        """
        # Get last sync versions
        local_version_info = self.sync_metadata.get("local_task_versions", {}).get(local_task.id, {})
        google_version_info = self.sync_metadata.get("google_task_versions", {}).get(google_task.id, {})
        
        # Compare modification times
        local_modified = local_task.modified_at or local_task.created_at
        google_modified = google_task.modified_at or google_task.created_at
        
        # If we have version info from last sync, use that for comparison
        if local_version_info and google_version_info:
            local_last_synced = local_version_info.get("modified_at")
            google_last_synced = google_version_info.get("modified_at")
            
            # If both were modified since last sync, we have a real conflict
            if (local_last_synced and local_modified > datetime.fromisoformat(local_last_synced) and
                google_last_synced and google_modified > datetime.fromisoformat(google_last_synced)):
                logger.warning(f"Conflict detected for task {local_task.id}")
                return "local"  # Default to local in case of conflict
        
        # Otherwise, use the more recently modified version
        if local_modified > google_modified:
            return "local"
        elif google_modified > local_modified:
            return "google"
        else:
            # If modified at the same time, default to local
            return "local"
    
    def _merge_tasks(self, local_task: Task, google_task: Task) -> Task:
        """
        Merge local and Google task fields.
        
        Args:
            local_task: Local task
            google_task: Google task
            
        Returns:
            Task: Merged task
        """
        # For now, we'll create a merged task that prioritizes local changes
        # but includes any Google-specific information not present locally
        merged_task = local_task.model_copy()
        
        # In a more sophisticated implementation, we could merge individual fields
        # based on which was more recently updated
        
        return merged_task
    
    def _update_task_versions(self, tasks: List[Task]):
        """
        Update task versions in sync metadata.
        
        Args:
            tasks: List of tasks to update versions for
        """
        local_versions = {}
        google_versions = {}
        
        for task in tasks:
            version_info = {
                "modified_at": (task.modified_at or task.created_at).isoformat(),
                "title": task.title
            }
            local_versions[task.id] = version_info
            google_versions[task.id] = version_info  # Same for now
        
        self.sync_metadata["local_task_versions"] = local_versions
        self.sync_metadata["google_task_versions"] = google_versions
    
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