#!/usr/bin/env python3
"""
Advanced Sync Manager - Enhanced synchronization between local tasks and Google Tasks
with support for push/pull operations and conflict resolution.
"""

import os
import sqlite3
import tempfile
import traceback
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
import hashlib
import json

from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.storage.local_storage import LocalStorage
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.utils.task_deduplication import create_task_signature, get_existing_task_signatures
from gtasks_cli.utils.datetime_utils import _normalize_datetime

logger = setup_logger(__name__)


class AdvancedSyncManager:
    """Advanced synchronization manager for Google Tasks with SQLite storage backend."""
    
    def __init__(self, storage, google_client, pull_range_days=None):
        """
        Initialize the AdvancedSyncManager.
        
        Args:
            storage: An instance of a storage backend (e.g., LocalStorage, SQLiteStorage)
            google_client: An instance of GoogleTasksClient
            pull_range_days: Number of days to look back for incremental sync (None for full sync)
        """
        self.local_storage = storage
        self.google_client = google_client
        self.pull_range_days = pull_range_days
        self.sync_metadata_file = os.path.join(
            os.path.expanduser("~"), ".gtasks", "advanced_sync_metadata.json"
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
            "last_push": None,
            "last_pull": None,
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
    
    def _remove_duplicates_from_list(self, tasks: List[Task]) -> List[Task]:
        """
        Remove duplicate tasks from a list based on their signatures.
        
        Args:
            tasks: List of tasks to deduplicate
            
        Returns:
            List[Task]: Deduplicated list of tasks
        """
        unique_tasks = []
        seen_signatures = set()
        duplicates_removed = 0
        
        for task in tasks:
            # Combine description and notes since the signature function only takes description
            description = (task.description or "") + (task.notes or "")
            task_signature = create_task_signature(
                title=task.title or "",
                description=description,
                due_date=task.due,
                status=task.status
            )
            
            if task_signature not in seen_signatures:
                unique_tasks.append(task)
                seen_signatures.add(task_signature)
                logger.debug(f"Adding unique task: {task.title} (ID: {task.id}) with signature: {task_signature}")
            else:
                duplicates_removed += 1
                logger.info(f"Removing duplicate task: {task.title} (ID: {task.id}) with signature: {task_signature}")
        
        logger.info(f"Removed {duplicates_removed} duplicate tasks during deduplication")
        return unique_tasks
    
    def sync(self, push_only: bool = False, pull_only: bool = False) -> bool:
        """
        Perform simplified bidirectional synchronization with Google Tasks using the 4-step approach.
        
        Args:
            push_only: If True, only push local changes to Google Tasks
            pull_only: If True, only pull changes from Google Tasks
            
        Returns:
            bool: True if sync was successful, False otherwise
        """
        logger.info("Starting simplified bidirectional synchronization process")
        
        try:
            # Connect to Google Tasks
            if not self.google_client.connect():
                logger.error("Failed to connect to Google Tasks")
                return False
            
            # Step 1: Pull all remote records once and save to memory
            logger.info("Step 1: Loading all Google Tasks into memory")
            all_google_tasks = self._load_all_google_tasks_once()
            if all_google_tasks is None:
                logger.error("Failed to load Google Tasks")
                return False
            
            logger.info(f"Loaded {len(all_google_tasks)} Google Tasks into memory")
            
            # Create a set of existing signatures for duplicate checking (only Google Tasks)
            google_signatures = set()
            for task in all_google_tasks:
                # Combine description and notes since the signature function only takes description
                description = (task.description or "") + (task.notes or "")
                signature = create_task_signature(
                    title=task.title or "",
                    description=description,
                    due_date=task.due,
                    status=task.status
                )
                google_signatures.add(signature)
            
            # Get local tasks
            local_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
            logger.info(f"Retrieved {len(local_tasks)} local tasks")
            
            # Create a set of local task signatures for duplicate checking
            local_signatures = set()
            for task in local_tasks:
                # Combine description and notes since the signature function only takes description
                description = (task.description or "") + (task.notes or "")
                signature = create_task_signature(
                    title=task.title or "",
                    description=description,
                    due_date=task.due,
                    status=task.status
                )
                local_signatures.add(signature)
            
            # Store the Google signatures for use in push operations to prevent duplicates
            self._google_signatures = google_signatures
            
            # Step 2: Compare records based on latest changes using cached versions
            logger.info("Step 2: Comparing records based on latest changes")
            sync_plan = self._compare_and_plan_changes_with_cache(local_tasks, all_google_tasks)
            
            # Short-circuit if there's nothing to do
            total_changes = sum(len(tasks) for tasks in sync_plan.values())
            if total_changes == 0:
                logger.info("No changes detected during sync comparison")
                return True
            
            logger.info(f"Sync plan summary before duplicate checking:")
            logger.info(f"  Tasks to update in remote: {len(sync_plan['update_remote'])}")
            logger.info(f"  Tasks to create in remote: {len(sync_plan['create_remote'])}")
            logger.info(f"  Tasks to update in local: {len(sync_plan['update_local'])}")
            logger.info(f"  Tasks to create in local: {len(sync_plan['create_local'])}")
            logger.info(f"  Local duplicates to remove: {len(sync_plan['remove_local_duplicates'])}")
            logger.info(f"  Remote duplicates to remove: {len(sync_plan['remove_remote_duplicates'])}")
            
            # Step 3: Check for duplicates and mark for removal
            logger.info("Step 3: Checking for duplicates")
            self._identify_and_mark_duplicates(sync_plan, local_tasks, all_google_tasks)
            
            # Re-check if there's anything to do after duplicate checking
            total_changes = sum(len(tasks) for tasks in sync_plan.values())
            logger.info(f"Total changes after duplicate checking: {total_changes}")
            
            if total_changes == 0:
                logger.info("No changes to sync after duplicate checking")
                return True
            
            # Step 4: Execute all changes
            logger.info("Step 4: Executing all changes")
            success = self._execute_sync_plan(sync_plan, push_only, pull_only)
            
            if success:
                logger.info("Simplified bidirectional synchronization completed successfully")
                # Update sync metadata
                self.sync_metadata["last_sync"] = datetime.utcnow().isoformat()
                self._save_sync_metadata()
                return True
            else:
                logger.error("Simplified bidirectional synchronization failed")
                return False
                
        except Exception as e:
            logger.error(f"Error during simplified synchronization: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _create_task_version(self, task: Task) -> str:
        """
        Create a version fingerprint for a task based on its key attributes.
        This helps detect actual changes vs. timestamp drift.
        
        Args:
            task: The task to create a version for
            
        Returns:
            str: A hash representing the task's key attributes
        """
        # Create a string with the key attributes that define a task's content
        key_attributes = [
            str(task.title),
            str(task.description or ""),
            str(task.notes or ""),
            str(task.due.isoformat() if task.due else ""),
            str(task.status.value if hasattr(task.status, 'value') else task.status),
            str(task.priority.value if hasattr(task.priority, 'value') else task.priority),
            str(task.project or ""),
            str(",".join(sorted(task.tags)) if task.tags else ""),
        ]
        
        # Create a hash of these attributes
        task_string = "|".join(key_attributes)
        return hashlib.md5(task_string.encode('utf-8')).hexdigest()
    
    def _load_all_google_tasks_once(self) -> List[Task]:
        """
        Load all Google Tasks into memory once to avoid multiple API calls.
        
        Returns:
            List[Task]: List of all Google Tasks, or None if failed
        """
        try:
            logger.info("Loading all Google Tasks into memory")
            
            # Get all tasklists
            tasklists = self.google_client.list_tasklists()
            if not tasklists:
                logger.error("Failed to retrieve tasklists from Google Tasks")
                return None
            
            # Create a mapping of tasklist IDs to titles
            tasklist_titles = {tl['id']: tl.get('title', 'Untitled List') for tl in tasklists}
            
            # Collect all tasks from all tasklists
            all_tasks = []
            
            # Determine if we should do incremental sync
            if self.pull_range_days is not None:
                # Calculate the minimum update time for incremental sync
                from datetime import datetime, timedelta, timezone
                min_update_time = datetime.now(timezone.utc) - timedelta(days=self.pull_range_days)
                min_update_time_iso = min_update_time.isoformat()
                
                logger.info(f"Performing incremental sync with {self.pull_range_days} day range (since {min_update_time_iso})")
                
                for tasklist in tasklists:
                    tasks = self.google_client.list_tasks_with_filters(
                        tasklist_id=tasklist['id'],
                        updated_min=min_update_time_iso,
                        show_completed=True,
                        show_hidden=True,
                        show_deleted=False
                    )
                    # Add tasklist information to each task
                    for task in tasks:
                        task.tasklist_id = tasklist['id']
                        # Add list title as well for display purposes
                        task.list_title = tasklist_titles.get(tasklist['id'], 'Untitled List')
                    all_tasks.extend(tasks)
            else:
                # Full sync - get all tasks
                logger.info("Performing full sync of all Google Tasks")
                for tasklist in tasklists:
                    tasks = self.google_client.list_tasks(
                        tasklist_id=tasklist['id'],
                        show_completed=True,
                        show_hidden=True,
                        show_deleted=False
                    )
                    # Add tasklist information to each task
                    for task in tasks:
                        task.tasklist_id = tasklist['id']
                        # Add list title as well for display purposes
                        task.list_title = tasklist_titles.get(tasklist['id'], 'Untitled List')
                    all_tasks.extend(tasks)
            
            logger.info(f"Successfully loaded {len(all_tasks)} tasks from Google Tasks")
            return all_tasks
            
        except Exception as e:
            logger.error(f"Error loading Google Tasks: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _compare_and_plan_changes(self, local_tasks: List[Task], google_tasks: List[Task]) -> Dict:
        """
        Compare local and remote tasks and plan synchronization changes.
        
        Args:
            local_tasks: List of local tasks
            google_tasks: List of Google Tasks
            
        Returns:
            Dict: Sync plan with tasks to update/create/delete
        """
        # Create dictionaries for quick lookup
        local_task_dict = {task.id: task for task in local_tasks}
        google_task_dict = {task.id: task for task in google_tasks}
        
        # Create signature maps for duplicate detection
        local_signature_map = self._create_signature_map(local_tasks)
        google_signature_map = self._create_signature_map(google_tasks)
        
        # Plan the changes
        sync_plan = {
            'update_remote': [],      # Local tasks that are newer than remote
            'create_remote': [],      # Local tasks that don't exist remotely
            'update_local': [],       # Remote tasks that are newer than local
            'create_local': [],       # Remote tasks that don't exist locally
            'remove_local_duplicates': [],
            'remove_remote_duplicates': [],
        }
        
        # Compare tasks by ID first
        all_task_ids = set(local_task_dict.keys()) | set(google_task_dict.keys())
        
        for task_id in all_task_ids:
            local_task = local_task_dict.get(task_id)
            google_task = google_task_dict.get(task_id)
            
            if local_task and google_task:
                # Task exists in both locations, compare modification times
                # Normalize both datetimes before comparison
                local_modified = _normalize_datetime(local_task.modified_at)
                google_modified = _normalize_datetime(google_task.modified_at)
                
                # If either datetime is None after normalization, treat as datetime.min
                if local_modified is None:
                    local_modified = datetime.min
                if google_modified is None:
                    google_modified = datetime.min
                
                # Only consider tasks as different if their modification times differ by more than a small threshold
                # This accounts for minor timestamp differences that might occur during sync operations
                time_difference = abs((local_modified - google_modified).total_seconds())
                
                if time_difference > 1:  # More than 1 second difference
                    if local_modified > google_modified:
                        # Local is newer, update remote
                        sync_plan['update_remote'].append(local_task)
                        logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - Local is newer (local: {local_modified}, remote: {google_modified})")
                    elif google_modified > local_modified:
                        # Remote is newer, update local
                        sync_plan['update_local'].append(google_task)
                        logger.debug(f"Task '{google_task.title}' (ID: {task_id}) - Remote is newer (local: {local_modified}, remote: {google_modified})")
                    else:
                        logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - No significant changes (modified: {local_modified})")
                else:
                    logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - No significant changes (time difference: {time_difference}s)")
            elif local_task:
                # Task only exists locally, check if it already exists remotely by signature
                # Combine description and notes since the signature function only takes description
                description = (local_task.description or "") + (local_task.notes or "")
                local_signature = create_task_signature(
                    title=local_task.title or "",
                    description=description,
                    due_date=local_task.due,
                    status=local_task.status
                )
                
                if local_signature in google_signature_map:
                    # Task already exists remotely, this is a duplicate
                    logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - Already exists remotely, skipping creation")
                else:
                    # Check if it was previously synced with Google Tasks (has a valid tasklist_id)
                    # Google Tasks tasklist IDs are long base64-like strings
                    # Only mark as deleted during full sync, not incremental sync
                    is_incremental_sync = self.pull_range_days is not None
                    if (hasattr(local_task, 'tasklist_id') and 
                        local_task.tasklist_id and 
                        len(local_task.tasklist_id) > 20 and
                        not is_incremental_sync):  # Only during full sync
                        # This task has a Google Tasks tasklist ID, which means it was previously synced
                        # Since it's no longer in Google Tasks during a full sync, it was likely deleted
                        # Mark it as deleted locally
                        logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - Previously synced with Google Tasks but no longer exists, marking as deleted locally")
                        local_task.status = TaskStatus.DELETED
                        sync_plan['remove_local_duplicates'].append(local_task)
                    elif (hasattr(local_task, 'tasklist_id') and 
                          local_task.tasklist_id and 
                          len(local_task.tasklist_id) > 20 and
                          is_incremental_sync):
                        # During incremental sync, skip tasks that were previously synced
                        # but are not in the current time window
                        logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - Previously synced, skipping during incremental sync")
                    else:
                        # Task doesn't exist remotely and wasn't previously synced, needs to be created
                        sync_plan['create_remote'].append(local_task)
                        logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - New local task")
            elif google_task:
                # Task only exists remotely, check if it already exists locally by signature
                # Combine description and notes since the signature function only takes description
                description = (google_task.description or "") + (google_task.notes or "")
                google_signature = create_task_signature(
                    title=google_task.title or "",
                    description=description,
                    due_date=google_task.due,
                    status=google_task.status
                )
                
                if google_signature in local_signature_map:
                    # Task already exists locally, this is a duplicate
                    logger.debug(f"Task '{google_task.title}' (ID: {task_id}) - Already exists locally, skipping creation")
                else:
                    # Task doesn't exist locally, needs to be created
                    sync_plan['create_local'].append(google_task)
                    logger.debug(f"Task '{google_task.title}' (ID: {task_id}) - New remote task")
        
        return sync_plan
    
    def _compare_and_plan_changes_with_cache(self, local_tasks: List[Task], google_tasks: List[Task]) -> Dict:
        """
        Compare local and remote tasks using cached versions for more efficient change detection.
        
        Args:
            local_tasks: List of local tasks
            google_tasks: List of Google Tasks
            
        Returns:
            Dict: Sync plan with tasks to update/create/delete
        """
        # Create dictionaries for quick lookup
        local_task_dict = {task.id: task for task in local_tasks}
        google_task_dict = {task.id: task for task in google_tasks}
        
        # Create signature maps for duplicate detection
        local_signature_map = self._create_signature_map(local_tasks)
        google_signature_map = self._create_signature_map(google_tasks)
        
        # Get cached task versions
        local_task_versions = self.sync_metadata.get("local_task_versions", {})
        google_task_versions = self.sync_metadata.get("google_task_versions", {})
        
        # Plan the changes
        sync_plan = {
            'update_remote': [],      # Local tasks that are newer than remote
            'create_remote': [],      # Local tasks that don't exist remotely
            'update_local': [],       # Remote tasks that are newer than local
            'create_local': [],       # Remote tasks that don't exist locally
            'remove_local_duplicates': [],
            'remove_remote_duplicates': [],
        }
        
        # Compare tasks by ID first
        all_task_ids = set(local_task_dict.keys()) | set(google_task_dict.keys())
        
        logger.debug(f"Total task IDs to compare: {len(all_task_ids)}")
        local_duplicates_count = 0
        
        for task_id in all_task_ids:
            local_task = local_task_dict.get(task_id)
            google_task = google_task_dict.get(task_id)
            
            if local_task and google_task:
                # Task exists in both locations, compare versions
                local_version = self._create_task_version(local_task)
                google_version = self._create_task_version(google_task)
                
                # Check cached versions
                cached_local_version = local_task_versions.get(task_id)
                cached_google_version = google_task_versions.get(task_id)
                
                # If versions have changed, determine which is newer based on modification time
                if local_version != cached_local_version or google_version != cached_google_version:
                    # Normalize both datetimes before comparison
                    local_modified = _normalize_datetime(local_task.modified_at)
                    google_modified = _normalize_datetime(google_task.modified_at)
                    
                    # If either datetime is None after normalization, treat as datetime.min
                    if local_modified is None:
                        local_modified = datetime.min
                    if google_modified is None:
                        google_modified = datetime.min
                    
                    # Only consider tasks as different if their modification times differ by more than a small threshold
                    # This accounts for minor timestamp differences that might occur during sync operations
                    time_difference = abs((local_modified - google_modified).total_seconds())
                    
                    if time_difference > 1:  # More than 1 second difference
                        if local_modified > google_modified:
                            # Local is newer, update remote
                            sync_plan['update_remote'].append(local_task)
                            logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - Local is newer (local: {local_modified}, remote: {google_modified})")
                        elif google_modified > local_modified:
                            # Remote is newer, update local
                            sync_plan['update_local'].append(google_task)
                            logger.debug(f"Task '{google_task.title}' (ID: {task_id}) - Remote is newer (local: {local_modified}, remote: {google_modified})")
                        else:
                            logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - No significant changes (modified: {local_modified})")
                    else:
                        logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - No significant changes (time difference: {time_difference}s)")
                else:
                    logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - No changes detected via version comparison")
                    
                # Update cached versions
                local_task_versions[task_id] = local_version
                google_task_versions[task_id] = google_version
            elif local_task:
                # Task only exists locally, check if it already exists remotely by signature
                # Combine description and notes since the signature function only takes description
                description = (local_task.description or "") + (local_task.notes or "")
                local_signature = create_task_signature(
                    title=local_task.title or "",
                    description=description,
                    due_date=local_task.due,
                    status=local_task.status
                )
                
                if local_signature in google_signature_map:
                    # Task already exists remotely, this is a duplicate
                    logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - Already exists remotely, skipping creation")
                else:
                    # Check if it was previously synced with Google Tasks (has a valid tasklist_id)
                    # Google Tasks tasklist IDs are long base64-like strings
                    # Only mark as deleted during full sync, not incremental sync
                    is_incremental_sync = self.pull_range_days is not None
                    if (hasattr(local_task, 'tasklist_id') and 
                        local_task.tasklist_id and 
                        len(local_task.tasklist_id) > 20 and
                        not is_incremental_sync):  # Only during full sync
                        # This task has a Google Tasks tasklist ID, which means it was previously synced
                        # Since it's no longer in Google Tasks during a full sync, it was likely deleted
                        # Mark it as deleted locally
                        logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - Previously synced with Google Tasks but no longer exists, marking as deleted locally")
                        local_task.status = TaskStatus.DELETED
                        sync_plan['remove_local_duplicates'].append(local_task)
                        local_duplicates_count += 1
                    elif (hasattr(local_task, 'tasklist_id') and 
                          local_task.tasklist_id and 
                          len(local_task.tasklist_id) > 20 and
                          is_incremental_sync):
                        # During incremental sync, skip tasks that were previously synced
                        # but are not in the current time window
                        logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - Previously synced, skipping during incremental sync")
                    else:
                        # Task doesn't exist remotely and wasn't previously synced, needs to be created
                        sync_plan['create_remote'].append(local_task)
                        logger.debug(f"Task '{local_task.title}' (ID: {task_id}) - New local task")
                        
                # Update cached version
                local_task_versions[task_id] = self._create_task_version(local_task)
            elif google_task:
                # Task only exists remotely, check if it already exists locally by signature
                # Combine description and notes since the signature function only takes description
                description = (google_task.description or "") + (google_task.notes or "")
                google_signature = create_task_signature(
                    title=google_task.title or "",
                    description=description,
                    due_date=google_task.due,
                    status=google_task.status
                )
                
                if google_signature in local_signature_map:
                    # Task already exists locally, this is a duplicate
                    logger.debug(f"Task '{google_task.title}' (ID: {task_id}) - Already exists locally, skipping creation")
                else:
                    # Task doesn't exist locally, needs to be created
                    sync_plan['create_local'].append(google_task)
                    logger.debug(f"Task '{google_task.title}' (ID: {task_id}) - New remote task")
                    
                # Update cached version
                google_task_versions[task_id] = self._create_task_version(google_task)
        
        logger.debug(f"Added {local_duplicates_count} tasks to remove_local_duplicates during comparison")
        
        # Update cached versions in metadata
        self.sync_metadata["local_task_versions"] = local_task_versions
        self.sync_metadata["google_task_versions"] = google_task_versions
        
        return sync_plan
    
    def _create_signature_map(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """
        Create a mapping of task signatures to tasks for duplicate detection.
        
        Args:
            tasks: List of tasks
            
        Returns:
            Dict[str, List[Task]]: Mapping of signatures to tasks
        """
        signature_map = {}
        for task in tasks:
            # Combine description and notes since the signature function only takes description
            description = (task.description or "") + (task.notes or "")
            signature = create_task_signature(
                title=task.title or "",
                description=description,
                due_date=task.due,
                status=task.status
            )
            if signature not in signature_map:
                signature_map[signature] = []
            signature_map[signature].append(task)
        return signature_map
    
    def _identify_and_mark_duplicates(self, sync_plan: Dict, local_tasks: List[Task], google_tasks: List[Task]):
        """
        Identify duplicate tasks and mark them for removal.
        
        Args:
            sync_plan: The sync plan to update
            local_tasks: List of local tasks
            google_tasks: List of Google tasks
        """
        # Find duplicates in local tasks
        local_signature_map = self._create_signature_map(local_tasks)
        duplicate_count = 0
        for signature, tasks in local_signature_map.items():
            if len(tasks) > 1:
                logger.debug(f"Found {len(tasks)} duplicate local tasks with signature {signature}")
                # Keep the first one, mark others for removal
                # But only mark tasks that are not already marked for other operations
                tasks_to_check = tasks[1:]  # Skip the first task (keep it)
                for task in tasks_to_check:
                    # Check if this task is already marked for another operation
                    is_already_handled = (
                        task in sync_plan['update_local'] or
                        task in sync_plan['create_local'] or
                        task in sync_plan['update_remote'] or
                        task in sync_plan['create_remote']
                    )
                    
                    if not is_already_handled:
                        sync_plan['remove_local_duplicates'].append(task)
                        duplicate_count += 1
                        logger.debug(f"Marking local task '{task.title}' (ID: {task.id}) for removal")
                        # Log additional details about why this task is considered a duplicate
                        logger.debug(f"  Duplicate details - Title: '{task.title}', Description: '{task.description}', Due: {task.due}, Status: {task.status}")
                    else:
                        logger.debug(f"Skipping duplicate task '{task.title}' (ID: {task.id}) as it's already being processed")
        
        # Find duplicates in remote tasks
        google_signature_map = self._create_signature_map(google_tasks)
        remote_duplicate_count = 0
        for signature, tasks in google_signature_map.items():
            if len(tasks) > 1:
                logger.debug(f"Found {len(tasks)} duplicate remote tasks with signature {signature}")
                # Keep the first one, mark others for removal
                # But only mark tasks that are not already marked for other operations
                tasks_to_check = tasks[1:]  # Skip the first task (keep it)
                for task in tasks_to_check:
                    # Check if this task is already marked for another operation
                    is_already_handled = (
                        task in sync_plan['update_local'] or
                        task in sync_plan['create_local'] or
                        task in sync_plan['update_remote'] or
                        task in sync_plan['create_remote']
                    )
                    
                    if not is_already_handled:
                        sync_plan['remove_remote_duplicates'].append(task)
                        remote_duplicate_count += 1
                        logger.debug(f"Marking remote task '{task.title}' (ID: {task.id}) for removal")
                        # Log additional details about why this task is considered a duplicate
                        logger.debug(f"  Duplicate details - Title: '{task.title}', Description: '{task.description}', Due: {task.due}, Status: {task.status}")
                    else:
                        logger.debug(f"Skipping duplicate remote task '{task.title}' (ID: {task.id}) as it's already being processed")
        
        if duplicate_count > 0 or remote_duplicate_count > 0:
            logger.info(f"Identified {duplicate_count} local and {remote_duplicate_count} remote duplicate tasks for removal")
    
    def _execute_sync_plan(self, sync_plan: Dict, push_only: bool, pull_only: bool) -> bool:
        """
        Execute the sync plan.
        
        Args:
            sync_plan: The sync plan to execute
            push_only: If True, only push changes
            pull_only: If True, only pull changes
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Handle push operations (if not pull_only)
            if not pull_only:
                logger.info("Executing push operations")
                push_success = self._execute_push_operations(sync_plan)
                if not push_success:
                    return False
            
            # Handle pull operations (if not push_only)
            if not push_only:
                logger.info("Executing pull operations")
                pull_success = self._execute_pull_operations(sync_plan)
                if not pull_success:
                    return False
            
            # Log summary
            logger.info("Sync execution summary:")
            logger.info(f"  Tasks to update in remote: {len(sync_plan['update_remote'])}")
            logger.info(f"  Tasks to create in remote: {len(sync_plan['create_remote'])}")
            logger.info(f"  Tasks to update in local: {len(sync_plan['update_local'])}")
            logger.info(f"  Tasks to create in local: {len(sync_plan['create_local'])}")
            logger.info(f"  Local duplicates removed: {len(sync_plan['remove_local_duplicates'])}")
            logger.info(f"  Remote duplicates removed: {len(sync_plan['remove_remote_duplicates'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing sync plan: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _execute_push_operations(self, sync_plan: Dict) -> bool:
        """
        Execute push operations (local to remote).
        
        Args:
            sync_plan: The sync plan
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Short-circuit if there's nothing to do
            if not any([
                len(sync_plan['remove_local_duplicates']),
                len(sync_plan['update_remote']),
                len(sync_plan['create_remote'])
            ]):
                logger.info("No push operations needed")
                return True
            
            # Remove local duplicates - we'll do this by marking them as deleted
            for task in sync_plan['remove_local_duplicates']:
                try:
                    # Use the storage's save_tasks method to update the task status
                    all_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
                    for t in all_tasks:
                        if t.id == task.id:
                            t.status = "deleted"
                            break
                    
                    # Save all tasks back
                    task_dicts = [t.model_dump() for t in all_tasks]
                    self.local_storage.save_tasks(task_dicts)
                    logger.debug(f"Marked duplicate local task as deleted: {task.title}")
                except Exception as e:
                    logger.warning(f"Failed to mark duplicate local task {task.title} as deleted: {e}")
            
            # Update remote tasks
            updated_tasks = []
            for task in sync_plan['update_remote']:
                try:
                    updated_task = self.google_client.update_task(task, task.tasklist_id)
                    if updated_task:
                        logger.debug(f"Updated task in Google: {task.title}")
                        updated_tasks.append(task)
                    else:
                        logger.warning(f"Failed to update task in Google: {task.title}")
                except Exception as e:
                    logger.error(f"Exception while updating task '{task.title}': {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Create remote tasks
            created_tasks = []
            for task in sync_plan['create_remote']:
                try:
                    # Create task in Google Tasks, passing Google signatures to prevent additional API calls
                    new_task = self.google_client.create_task(task, self._google_signatures)
                    if new_task:
                        logger.debug(f"Created new task in Google: {task.title}")
                        # Update local task with new ID from Google
                        task.id = new_task.id
                        # Update tasklist_id if it doesn't exist
                        if not hasattr(task, 'tasklist_id') or not task.tasklist_id:
                            task.tasklist_id = new_task.tasklist_id
                            
                        # Update the task in local storage
                        all_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
                        # Find and replace the task with the updated one
                        for i, t in enumerate(all_tasks):
                            if t.id == task.id:
                                all_tasks[i] = task
                                break
                        else:
                            # If not found, add it
                            all_tasks.append(task)
                            
                        task_dicts = [t.model_dump() for t in all_tasks]
                        self.local_storage.save_tasks(task_dicts)
                        
                        # Add the new task's signature to our Google signatures set to prevent future duplicates
                        description = (task.description or "") + (task.notes or "")
                        signature = create_task_signature(
                            title=task.title or "",
                            description=description,
                            due_date=task.due,
                            status=task.status
                        )
                        self._google_signatures.add(signature)
                        
                        created_tasks.append(task)
                    else:
                        logger.warning(f"Failed to create task in Google: {task.title}")
                except Exception as e:
                    logger.error(f"Exception while creating task '{task.title}': {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Update list mappings only for tasks that were actually modified
            if updated_tasks or created_tasks:
                list_mappings = self.local_storage.load_list_mapping()
                new_list_mapping = list_mappings.copy()
                
                # Update list mappings for updated tasks
                for task in updated_tasks:
                    if hasattr(task, 'tasklist_id') and task.tasklist_id:
                        # Get the task list title from Google
                        list_title = self.google_client.get_tasklist_title(task.tasklist_id)
                        if list_title:
                            new_list_mapping[task.id] = list_title
                
                # Update list mappings for created tasks
                for task in created_tasks:
                    if hasattr(task, 'tasklist_id') and task.tasklist_id:
                        # Get the task list title from Google
                        list_title = self.google_client.get_tasklist_title(task.tasklist_id)
                        if list_title:
                            new_list_mapping[task.id] = list_title
                
                # Save updated list mappings
                self.local_storage.save_list_mapping(new_list_mapping)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during push operations: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _execute_pull_operations(self, sync_plan: Dict) -> bool:
        """
        Execute pull operations (remote to local).
        
        Args:
            sync_plan: The sync plan
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Short-circuit if there's nothing to do
            if not any([
                len(sync_plan['remove_remote_duplicates']),
                len(sync_plan['update_local']),
                len(sync_plan['create_local'])
            ]):
                logger.info("No pull operations needed")
                return True
            
            # Remove remote duplicates - actually delete them from Google Tasks
            deleted_remote_count = 0
            for task in sync_plan['remove_remote_duplicates']:
                try:
                    # Delete the task from Google Tasks
                    if self.google_client.delete_task(task.id, task.tasklist_id):
                        logger.debug(f"Deleted duplicate remote task: {task.title} (ID: {task.id})")
                        deleted_remote_count += 1
                    else:
                        logger.warning(f"Failed to delete duplicate remote task: {task.title} (ID: {task.id})")
                except Exception as e:
                    logger.error(f"Exception while deleting remote task '{task.title}' (ID: {task.id}): {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            if deleted_remote_count > 0:
                logger.info(f"Deleted {deleted_remote_count} duplicate remote tasks from Google Tasks")
            
            # Remove local duplicates (including deleted tasks that no longer exist in Google Tasks)
            deleted_local_count = 0
            for task in sync_plan['remove_local_duplicates']:
                try:
                    if task.status == TaskStatus.DELETED:
                        # Actually delete the task from local storage
                        all_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
                        # Filter out the deleted task
                        remaining_tasks = [t for t in all_tasks if t.id != task.id]
                        # Save the remaining tasks
                        task_dicts = [t.model_dump() for t in remaining_tasks]
                        self.local_storage.save_tasks(task_dicts)
                        logger.debug(f"Deleted local task that no longer exists in Google Tasks: {task.title} (ID: {task.id})")
                        deleted_local_count += 1
                    else:
                        # Mark as deleted but keep in storage
                        all_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
                        # Find and update the specific task
                        for i, t in enumerate(all_tasks):
                            if t.id == task.id:
                                all_tasks[i].status = TaskStatus.DELETED
                                break
                        # Save all tasks
                        task_dicts = [t.model_dump() for t in all_tasks]
                        self.local_storage.save_tasks(task_dicts)
                        logger.debug(f"Marked local duplicate task as deleted: {task.title} (ID: {task.id})")
                        deleted_local_count += 1
                except Exception as e:
                    logger.error(f"Exception while handling local task '{task.title}' (ID: {task.id}): {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            if deleted_local_count > 0:
                logger.info(f"Handled {deleted_local_count} local tasks (deleted or marked as duplicates)")
            
            # Update local tasks
            updated_tasks = []
            for task in sync_plan['update_local']:
                try:
                    # Load all tasks
                    all_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
                    # Find and update the specific task
                    for i, t in enumerate(all_tasks):
                        if t.id == task.id:
                            all_tasks[i] = task
                            break
                    else:
                        # If not found, add it
                        all_tasks.append(task)
                    
                    # Save all tasks
                    task_dicts = [t.model_dump() for t in all_tasks]
                    self.local_storage.save_tasks(task_dicts)
                    updated_tasks.append(task)
                    logger.debug(f"Updated local task: {task.title}")
                except Exception as e:
                    logger.error(f"Exception while updating local task '{task.title}': {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Create local tasks
            created_tasks = []
            for task in sync_plan['create_local']:
                try:
                    # Load all tasks
                    all_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
                    # Add the new task
                    all_tasks.append(task)
                    
                    # Save all tasks
                    task_dicts = [t.model_dump() for t in all_tasks]
                    self.local_storage.save_tasks(task_dicts)
                    created_tasks.append(task)
                    logger.debug(f"Created local task: {task.title}")
                except Exception as e:
                    logger.error(f"Exception while creating local task '{task.title}': {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Save synchronized tasks locally
            all_pulled_tasks = updated_tasks + created_tasks
            
            # Final deduplication pass to ensure no duplicates
            unique_tasks = self._remove_duplicates_from_list(all_pulled_tasks)
            
            # Create and save the list mapping only if we have tasks
            if unique_tasks or updated_tasks:
                list_mappings = self.local_storage.load_list_mapping()
                new_list_mapping = list_mappings.copy()  # Start with existing mappings
                
                # Update list mappings with any new tasklist IDs
                for task in unique_tasks:
                    if hasattr(task, 'tasklist_id') and task.tasklist_id:
                        # Update mapping with tasklist ID if it's not already there
                        list_name = getattr(task, 'list_title', None)
                        if not list_name:
                            # Get the list title from Google if not already set
                            list_name = self.google_client.get_tasklist_title(task.tasklist_id)
                        
                        if list_name:
                            new_list_mapping[task.id] = list_name
                
                # Also update list mappings for updated tasks
                for task in updated_tasks:
                    if hasattr(task, 'tasklist_id') and task.tasklist_id:
                        list_name = getattr(task, 'list_title', None)
                        if not list_name:
                            # Get the list title from Google if not already set
                            list_name = self.google_client.get_tasklist_title(task.tasklist_id)
                        
                        if list_name:
                            new_list_mapping[task.id] = list_name
                
                # Save updated list mappings
                self.local_storage.save_list_mapping(new_list_mapping)
            
            logger.info(f"Pull operations completed: {len(updated_tasks)} updated, {len(created_tasks)} created, {deleted_local_count} local tasks handled, {deleted_remote_count} duplicates deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error during pull operations: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def push_to_google(self) -> bool:
        """
        Push local changes to Google Tasks.
        Only uploads local tasks that don't exist in Google or are newer than Google versions.
        
        Returns:
            bool: True if push was successful, False otherwise
        """
        logger.info("Starting push to Google Tasks process")
        
        # Use the simplified sync approach with push_only flag
        return self.sync(push_only=True, pull_only=False)
    
    def pull_from_google(self) -> bool:
        """
        Pull changes from Google Tasks to local storage.
        Only downloads Google tasks that don't exist locally or are newer than local versions.
        
        Returns:
            bool: True if pull was successful, False otherwise
        """
        logger.info("Starting pull from Google Tasks process")
        
        # Use the simplified sync approach with pull_only flag
        return self.sync(push_only=False, pull_only=True)

    def sync_single_task(self, task: Task, operation: str, old_task_id: str = None) -> bool:
        """
        Sync a single task immediately with Google Tasks.
        
        Args:
            task: The task to sync
            operation: The operation performed ('create', 'update', 'delete')
            old_task_id: The original local ID of the task (required for 'create' operation if ID changes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Auto-saving task '{task.title}' (Operation: {operation})")
            
            # Connect to Google Tasks
            if not self.google_client.connect():
                logger.error("Failed to connect to Google Tasks")
                return False
            
            # Load sync metadata if not already loaded
            if not self.sync_metadata:
                self.sync_metadata = self._load_sync_metadata()
            
            local_task_versions = self.sync_metadata.get("local_task_versions", {})
            google_task_versions = self.sync_metadata.get("google_task_versions", {})
            
            success = False
            
            if operation == 'create':
                # Create task in Google Tasks
                # We pass an empty set for signatures as we don't have them loaded efficiently here
                # and we assume the user wants to create this specific task.
                new_task = self.google_client.create_task(task, set())
                
                if new_task:
                    logger.info(f"Auto-saved new task to Google: {task.title} (ID: {new_task.id})")
                    
                    # If ID changed (which it likely did from UUID to Google ID)
                    if task.id != new_task.id:
                        # Delete the old task from local storage
                        if old_task_id:
                            self.local_storage.delete_task(old_task_id)
                        else:
                            # If old_task_id not provided, try to delete by current task.id (which might be the UUID)
                            self.local_storage.delete_task(task.id)
                            
                        # Update local task object with new ID and other fields from Google
                        task.id = new_task.id
                        if not hasattr(task, 'tasklist_id') or not task.tasklist_id:
                            task.tasklist_id = new_task.tasklist_id
                            
                        # Save the updated task to local storage
                        # We use save_tasks which upserts
                        self.local_storage.save_tasks([task.model_dump()])
                        
                        # Update list mapping if needed
                        if hasattr(task, 'tasklist_id') and task.tasklist_id:
                            list_title = self.google_client.get_tasklist_title(task.tasklist_id)
                            if list_title:
                                self.local_storage.save_list_mapping({task.id: list_title})
                                
                    success = True
                    
            elif operation == 'update':
                updated_task = self.google_client.update_task(task, task.tasklist_id)
                if updated_task:
                    logger.info(f"Auto-saved updated task to Google: {task.title}")
                    success = True
                    
            elif operation == 'delete':
                # For delete, we need the tasklist_id. If it's missing, we can't delete from Google efficiently
                if hasattr(task, 'tasklist_id') and task.tasklist_id:
                    if self.google_client.delete_task(task.id, task.tasklist_id):
                        logger.info(f"Auto-saved deleted task from Google: {task.title}")
                        success = True
                else:
                    logger.warning(f"Cannot auto-save delete for task '{task.title}': Missing tasklist_id")
                    # If it doesn't have a tasklist_id, maybe it was never synced?
                    # In that case, success = True effectively (nothing to delete remotely)
                    success = True
            
            if success:
                # Update metadata
                if operation == 'delete':
                    if task.id in local_task_versions:
                        del local_task_versions[task.id]
                    if task.id in google_task_versions:
                        del google_task_versions[task.id]
                else:
                    # Calculate new version
                    version = self._create_task_version(task)
                    local_task_versions[task.id] = version
                    google_task_versions[task.id] = version
                
                self.sync_metadata["local_task_versions"] = local_task_versions
                self.sync_metadata["google_task_versions"] = google_task_versions
                self.sync_metadata["last_sync"] = datetime.utcnow().isoformat()
                self._save_sync_metadata()
                
                return True
                
        except Exception as e:
            logger.error(f"Error during auto-save: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
        
        return False

    def sync_multiple_tasks(self, tasks: List[Task], operation: str) -> bool:
        """
        Sync multiple tasks immediately with Google Tasks.
        
        Args:
            tasks: List of tasks to sync
            operation: The operation performed ('create', 'update', 'delete')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Auto-saving {len(tasks)} tasks (Operation: {operation})")
            
            # Connect to Google Tasks
            if not self.google_client.connect():
                logger.error("Failed to connect to Google Tasks")
                return False
            
            # Load sync metadata if not already loaded
            if not self.sync_metadata:
                self.sync_metadata = self._load_sync_metadata()
            
            local_task_versions = self.sync_metadata.get("local_task_versions", {})
            google_task_versions = self.sync_metadata.get("google_task_versions", {})
            
            success_count = 0
            
            for task in tasks:
                task_success = False
                
                if operation == 'create':
                    # Create task in Google Tasks
                    new_task = self.google_client.create_task(task, set())
                    
                    if new_task:
                        logger.debug(f"Auto-saved new task to Google: {task.title} (ID: {new_task.id})")
                        
                        # If ID changed (which it likely did from UUID to Google ID)
                        if task.id != new_task.id:
                            old_id = task.id
                            # Delete the old task from local storage
                            self.local_storage.delete_task(old_id)
                                
                            # Update local task object with new ID and other fields from Google
                            task.id = new_task.id
                            if not hasattr(task, 'tasklist_id') or not task.tasklist_id:
                                task.tasklist_id = new_task.tasklist_id
                                
                            # Save the updated task to local storage
                            self.local_storage.save_tasks([task.model_dump()])
                            
                            # Update list mapping if needed
                            if hasattr(task, 'tasklist_id') and task.tasklist_id:
                                list_title = self.google_client.get_tasklist_title(task.tasklist_id)
                                if list_title:
                                    self.local_storage.save_list_mapping({task.id: list_title})
                                    
                        task_success = True
                        
                elif operation == 'update':
                    updated_task = self.google_client.update_task(task, task.tasklist_id)
                    if updated_task:
                        logger.debug(f"Auto-saved updated task to Google: {task.title}")
                        task_success = True
                        
                elif operation == 'delete':
                    if hasattr(task, 'tasklist_id') and task.tasklist_id:
                        if self.google_client.delete_task(task.id, task.tasklist_id):
                            logger.debug(f"Auto-saved deleted task from Google: {task.title}")
                            task_success = True
                    else:
                        logger.warning(f"Cannot auto-save delete for task '{task.title}': Missing tasklist_id")
                        task_success = True
                
                if task_success:
                    success_count += 1
                    # Update metadata
                    if operation == 'delete':
                        if task.id in local_task_versions:
                            del local_task_versions[task.id]
                        if task.id in google_task_versions:
                            del google_task_versions[task.id]
                    else:
                        # Calculate new version
                        version = self._create_task_version(task)
                        local_task_versions[task.id] = version
                        google_task_versions[task.id] = version
            
            # Save metadata once after all updates
            self.sync_metadata["local_task_versions"] = local_task_versions
            self.sync_metadata["google_task_versions"] = google_task_versions
            self.sync_metadata["last_sync"] = datetime.utcnow().isoformat()
            self._save_sync_metadata()
            
            logger.info(f"Auto-save completed: {success_count}/{len(tasks)} tasks synced")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error during bulk auto-save: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False