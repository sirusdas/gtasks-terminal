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
from gtasks_cli.models.task import Task
from gtasks_cli.storage.local_storage import LocalStorage
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
from gtasks_cli.utils.task_deduplication import create_task_signature, get_existing_task_signatures
from gtasks_cli.utils.datetime_utils import _normalize_datetime

logger = setup_logger(__name__)


class AdvancedSyncManager:
    """Manages advanced synchronization between local tasks and Google Tasks with conflict resolution."""
    
    def __init__(self, storage, google_client):
        """
        Initialize the AdvancedSyncManager.
        
        Args:
            storage: An instance of a storage backend (e.g., LocalStorage, SQLiteStorage)
            google_client: An instance of GoogleTasksClient
        """
        self.local_storage = storage
        self.google_client = google_client
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
            task_signature = create_task_signature(
                title=task.title or "",
                description=task.description or "",
                due_date=task.due,
                status=task.status,
                notes=task.notes or ""
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
    
    def push_to_google(self) -> bool:
        """
        Push local changes to Google Tasks.
        Only uploads local tasks that don't exist in Google or are newer than Google versions.
        
        Returns:
            bool: True if push was successful, False otherwise
        """
        logger.info("Starting push to Google Tasks process with optimized temporary database approach")
        
        # Connect to Google Tasks
        if not self.google_client.connect():
            logger.error("Failed to connect to Google Tasks")
            return False
        
        temp_db_path = None
        try:
            # Create temporary database for optimized operations
            temp_db_path = self._create_temp_database()
            
            # Set the temp_db_path attribute so other methods can use it
            self._temp_db_path = temp_db_path
            
            # Load all Google Tasks into temporary database once
            google_task_count = self._load_google_tasks_to_temp_db(temp_db_path)
            logger.info(f"Loaded {google_task_count} Google Tasks into temporary database for push operation")
            
            # Load local tasks
            local_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
            logger.debug(f"Loaded {len(local_tasks)} local tasks")
            
            # Load list mappings for local tasks
            list_mappings = self.local_storage.load_list_mapping()
            
            # Create a mapping of tasklist titles to IDs from temporary database
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT tasklist_id FROM temp_google_tasks')
            tasklist_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Create tasklist title to ID mapping (simplified for now)
            tasklists = self.google_client.list_tasklists()
            tasklist_title_to_id = {tasklist['title']: tasklist['id'] for tasklist in tasklists}
            
            # Get existing task signatures from temporary database to prevent duplicates
            try:
                # Create signatures from tasks in temporary database
                conn = sqlite3.connect(temp_db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT title, description, due, status FROM temp_google_tasks
                ''')
                
                existing_signatures = set()
                rows = cursor.fetchall()
                for row in rows:
                    title = row[0] or ""
                    description = row[1] or ""
                    due_date = row[2] or ""
                    status = row[3] or ""
                    signature = self._create_task_signature(title, description, due_date, status)
                    existing_signatures.add(signature)
                
                conn.close()
                logger.debug(f"Retrieved {len(existing_signatures)} existing task signatures from temporary database")
            except Exception as e:
                logger.error(f"Failed to retrieve existing task signatures from temporary database: {e}")
                logger.warning("Cannot perform duplicate checking due to database issues. Aborting push to prevent duplicates.")
                return False
            
            # Push local tasks to Google using temporary database for reference
            # For now, we'll use the existing _push_local_tasks method but with data from our temp database
            # In a full implementation, we would replace this with _push_local_tasks_optimized
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, description, due, priority, status, project, tags, notes,
                       dependencies, recurrence_rule, created_at, modified_at, tasklist_id
                FROM temp_google_tasks
            ''')
            
            rows = cursor.fetchall()
            all_google_tasks = []
            
            for row in rows:
                # Convert row to Task object
                task_dict = {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'due': datetime.fromisoformat(row[3]) if row[3] else None,
                    'priority': row[4],
                    'status': row[5],
                    'project': row[6],
                    'tags': json.loads(row[7]) if row[7] else [],
                    'notes': row[8],
                    'dependencies': json.loads(row[9]) if row[9] else [],
                    'recurrence_rule': row[10],
                    'created_at': datetime.fromisoformat(row[11]) if row[11] else None,
                    'modified_at': datetime.fromisoformat(row[12]) if row[12] else None,
                    'tasklist_id': row[13]
                }
                
                try:
                    task = Task(**task_dict)
                    all_google_tasks.append(task)
                except Exception as e:
                    logger.error(f"Failed to create task from database row: {e}")
                    continue
            
            conn.close()
            
            # Use the existing push logic but with data from our temporary database
            pushed_tasks = self._push_local_tasks(local_tasks, all_google_tasks, list_mappings, 
                                                tasklist_title_to_id, existing_signatures)
            
            # Update sync metadata
            self.sync_metadata["last_push"] = datetime.utcnow().isoformat()
            self._save_sync_metadata()
            
            logger.info("Push to Google Tasks completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Push to Google Tasks failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
        finally:
            # Clean up temporary database
            if temp_db_path and os.path.exists(temp_db_path):
                try:
                    os.unlink(temp_db_path)
                    logger.debug(f"Cleaned up temporary database: {temp_db_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary database {temp_db_path}: {e}")
            
            # Clear the temp_db_path attribute
            if hasattr(self, '_temp_db_path'):
                delattr(self, '_temp_db_path')
    
    def pull_from_google(self) -> bool:
        """
        Pull changes from Google Tasks to local storage.
        Only downloads Google tasks that don't exist locally or are newer than local versions.
        
        Returns:
            bool: True if pull was successful, False otherwise
        """
        logger.info("Starting pull from Google Tasks process")
        
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
            
            # Create mappings
            tasklist_id_to_title = {tasklist['id']: tasklist['title'] for tasklist in tasklists}
            
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
            
            # Pull Google tasks to local
            pulled_tasks = self._pull_google_tasks(local_tasks, all_google_tasks, tasklist_id_to_title)
            
            # Final deduplication pass to ensure no duplicates
            unique_tasks = self._remove_duplicates_from_list(pulled_tasks)
            
            # Save synchronized tasks locally
            task_dicts = [task.model_dump() for task in unique_tasks]
            self.local_storage.save_tasks(task_dicts)

            # Create and save the list mapping
            new_list_mapping = {}
            for task in unique_tasks:
                if task.tasklist_id in tasklist_id_to_title:
                    new_list_mapping[task.id] = tasklist_id_to_title[task.tasklist_id]
            self.local_storage.save_list_mapping(new_list_mapping)
            
            # Update sync metadata
            self.sync_metadata["last_pull"] = datetime.utcnow().isoformat()
            self._save_sync_metadata()
            
            logger.info("Pull from Google Tasks completed successfully")
            return True
            
        except google.auth.exceptions.TransportError as e:
            logger.error("Authentication failed during pull from Google Tasks: TransportError")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
        except google.auth.exceptions.RefreshError as e:
            logger.error("Authentication failed during pull from Google Tasks: RefreshError")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
        except google.auth.exceptions.DefaultCredentialsError as e:
            logger.error("Authentication failed during pull from Google Tasks: DefaultCredentialsError")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during pull from Google Tasks: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def sync(self) -> bool:
        """
        Perform bidirectional synchronization between local and Google tasks using temporary database.
        Resolves conflicts by keeping the most recently modified version.
        
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        logger.info("Starting bidirectional synchronization process with temporary database")
        
        # Connect to Google Tasks
        if not self.google_client.connect():
            logger.error("Failed to connect to Google Tasks")
            return False
        
        temp_db_path = None
        try:
            # Create temporary database
            temp_db_path = self._create_temp_database()
            
            # Set the temp_db_path attribute so other methods can use it
            self._temp_db_path = temp_db_path
            
            # Load all Google Tasks into temporary database
            google_task_count = self._load_google_tasks_to_temp_db(temp_db_path)
            logger.info(f"Loaded {google_task_count} Google Tasks into temporary database")
            
            # Load local tasks
            local_tasks = [Task(**task_dict) for task_dict in self.local_storage.load_tasks()]
            logger.debug(f"Loaded {len(local_tasks)} local tasks")
            
            # Load list mappings for local tasks
            list_mappings = self.local_storage.load_list_mapping()
            
            # Create mappings from temporary database
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # Get tasklists from Google (we still need this for mapping)
            tasklists = self.google_client.list_tasklists()
            tasklist_title_to_id = {tasklist['title']: tasklist['id'] for tasklist in tasklists}
            tasklist_id_to_title = {tasklist['id']: tasklist['title'] for tasklist in tasklists}
            
            # Load all Google Tasks from temporary database
            cursor.execute('''
                SELECT id, title, description, due, priority, status, project, tags, notes,
                       dependencies, recurrence_rule, created_at, modified_at, tasklist_id
                FROM temp_google_tasks
            ''')
            
            rows = cursor.fetchall()
            all_google_tasks = []
            
            for row in rows:
                # Convert row to Task object
                task_dict = {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'due': datetime.fromisoformat(row[3]) if row[3] else None,
                    'priority': row[4],
                    'status': row[5],
                    'project': row[6],
                    'tags': json.loads(row[7]) if row[7] else [],
                    'notes': row[8],
                    'dependencies': json.loads(row[9]) if row[9] else [],
                    'recurrence_rule': row[10],
                    'created_at': datetime.fromisoformat(row[11]) if row[11] else None,
                    'modified_at': datetime.fromisoformat(row[12]) if row[12] else None,
                    'tasklist_id': row[13]
                }
                
                try:
                    task = Task(**task_dict)
                    # Add tasklist information to each task
                    task.tasklist_id = row[13]
                    all_google_tasks.append(task)
                except Exception as e:
                    logger.error(f"Failed to create task from database row: {e}")
                    continue
            
            conn.close()
            
            logger.debug(f"Loaded total of {len(all_google_tasks)} Google tasks from temporary database")
            
            # Get existing task signatures to prevent duplicates
            try:
                # Create signatures from tasks in temporary database
                conn = sqlite3.connect(temp_db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT title, description, due, status FROM temp_google_tasks
                ''')
                
                existing_signatures = set()
                rows = cursor.fetchall()
                for row in rows:
                    title = row[0] or ""
                    description = row[1] or ""
                    due_date = row[2] or ""
                    status = row[3] or ""
                    signature = self._create_task_signature(title, description, due_date, status)
                    existing_signatures.add(signature)
                
                conn.close()
                logger.debug(f"Retrieved {len(existing_signatures)} existing task signatures from temporary database")
            except Exception as e:
                logger.error(f"Failed to retrieve existing task signatures from temporary database: {e}")
                logger.warning("Cannot perform duplicate checking due to database issues. Aborting sync to prevent duplicates.")
                return False
            
            # First, push local changes
            logger.info("Pushing local changes to Google Tasks")
            logger.debug(f"About to call _push_local_tasks with {len(local_tasks)} local tasks and {len(all_google_tasks)} Google tasks")
            pushed_tasks = self._push_local_tasks(local_tasks, all_google_tasks, list_mappings, 
                                                tasklist_title_to_id, existing_signatures)
            
            # Reload Google Tasks after push into temporary database
            logger.info("Reloading Google Tasks into temporary database after push operations")
            google_task_count = self._load_google_tasks_to_temp_db(temp_db_path)
            logger.info(f"Reloaded {google_task_count} Google Tasks into temporary database")
            
            # Load updated Google Tasks from temporary database
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, description, due, priority, status, project, tags, notes,
                       dependencies, recurrence_rule, created_at, modified_at, tasklist_id
                FROM temp_google_tasks
            ''')
            
            rows = cursor.fetchall()
            all_google_tasks = []
            
            for row in rows:
                task_dict = {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'due': datetime.fromisoformat(row[3]) if row[3] else None,
                    'priority': row[4],
                    'status': row[5],
                    'project': row[6],
                    'tags': json.loads(row[7]) if row[7] else [],
                    'notes': row[8],
                    'dependencies': json.loads(row[9]) if row[9] else [],
                    'recurrence_rule': row[10],
                    'created_at': datetime.fromisoformat(row[11]) if row[11] else None,
                    'modified_at': datetime.fromisoformat(row[12]) if row[12] else None,
                    'tasklist_id': row[13]
                }
                
                try:
                    task = Task(**task_dict)
                    # Add tasklist information to each task
                    task.tasklist_id = row[13]
                    all_google_tasks.append(task)
                except Exception as e:
                    logger.error(f"Failed to create task from database row: {e}")
                    continue
            
            conn.close()
            
            # Then, pull remote changes
            logger.info("Pulling changes from Google Tasks")
            pulled_tasks = self._pull_google_tasks(local_tasks, all_google_tasks, tasklist_id_to_title)
            
            # Final deduplication pass to ensure no duplicates
            unique_tasks = self._remove_duplicates_from_list(pulled_tasks)
            
            # Save synchronized tasks locally
            task_dicts = [task.model_dump() for task in unique_tasks]
            self.local_storage.save_tasks(task_dicts)

            # Create and save the list mapping
            new_list_mapping = {}
            for task in unique_tasks:
                if task.tasklist_id in tasklist_id_to_title:
                    new_list_mapping[task.id] = tasklist_id_to_title[task.tasklist_id]
            self.local_storage.save_list_mapping(new_list_mapping)
            
            # Update sync metadata
            self.sync_metadata["last_sync"] = datetime.utcnow().isoformat()
            self._save_sync_metadata()
            
            # Log sync summary
            logger.info("Bidirectional synchronization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error during bidirectional synchronization: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
        finally:
            # Clean up temporary database
            if temp_db_path and os.path.exists(temp_db_path):
                try:
                    os.unlink(temp_db_path)
                    logger.debug(f"Cleaned up temporary database: {temp_db_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary database {temp_db_path}: {e}")
            
            # Clear the temp_db_path attribute
            if hasattr(self, '_temp_db_path'):
                delattr(self, '_temp_db_path')
    
    def _push_local_tasks(self, local_tasks: List[Task], google_tasks: List[Task],
                         list_mappings: Dict[str, str], tasklist_title_to_id: Dict[str, str],
                         existing_signatures: set) -> List[Task]:
        """
        Push local tasks to Google Tasks.
        
        Args:
            local_tasks: List of local tasks
            google_tasks: List of Google tasks
            list_mappings: Mapping of local task IDs to list names
            tasklist_title_to_id: Mapping of tasklist titles to IDs
            existing_signatures: Set of existing task signatures to prevent duplicates
            
        Returns:
            List[Task]: List of tasks after push operation
        """
        print("=== ENTERING _push_local_tasks METHOD ===")
        logger.debug("****************************************")
        logger.debug("=== ENTERING _push_local_tasks METHOD ===")
        logger.debug("****************************************")
        logger.debug(f"Number of local tasks: {len(local_tasks)}")
        logger.debug(f"Number of Google tasks: {len(google_tasks)}")
        logger.debug(f"Number of existing signatures: {len(existing_signatures)}")
        
        # Create mappings for easier lookup
        google_task_dict = {task.id: task for task in google_tasks}
        google_signature_to_task = {}
        
        for task in google_tasks:
            signature = create_task_signature(
                title=task.title or "",
                description=task.description or "",
                due_date=task.due,
                status=task.status,
                notes=task.notes or ""
            )
            google_signature_to_task[signature] = task
        
        logger.debug(f"Created Google task mappings: {len(google_task_dict)} by ID, {len(google_signature_to_task)} by signature")
        
        # Debug: Check if apple signature is in google_signature_to_task
        apple_signature = create_task_signature("apple", "", "", "pending")
        logger.debug(f"Apple signature: {apple_signature}")
        logger.debug(f"Is apple signature in google_signature_to_task? {apple_signature in google_signature_to_task}")
        if apple_signature in google_signature_to_task:
            apple_task = google_signature_to_task[apple_signature]
            logger.debug(f"Found apple task in google_signature_to_task: ID={apple_task.id}")
        
        # Debug: Check if apple signature is in existing_signatures
        logger.debug(f"Is apple signature in existing_signatures? {apple_signature in existing_signatures}")
        
        # Process local tasks - upload new or updated tasks to Google
        tasks_created = 0
        tasks_updated = 0
        tasks_skipped = 0
        tasks_failed_auth = 0
        tasks_duplicate_check_failed = 0
        
        # Count apple tasks in local tasks
        apple_tasks = [task for task in local_tasks if task.title == "apple"]
        logger.debug(f"Number of local apple tasks: {len(apple_tasks)}")
        for i, apple_task in enumerate(apple_tasks):
            logger.debug(f"Local apple task {i+1}: ID={apple_task.id}, Title={apple_task.title}")
        
        for local_task in local_tasks:
            local_signature = create_task_signature(
                title=local_task.title or "",
                description=local_task.description or "",
                due_date=local_task.due,
                status=local_task.status,
                notes=local_task.notes or ""
            )
            
            logger.debug(f"Processing local task '{local_task.title}' (ID: {local_task.id}) with signature: {local_signature}")
            
            # Determine which tasklist this task should be in
            tasklist_name = list_mappings.get(local_task.id, "My Tasks")
            tasklist_id = tasklist_title_to_id.get(tasklist_name)
            
            # If tasklist doesn't exist, use default
            if not tasklist_id:
                tasklist_id = "@default"
                logger.debug(f"Using default tasklist for task '{local_task.title}'")
            else:
                logger.debug(f"Using tasklist '{tasklist_name}' (ID: {tasklist_id}) for task '{local_task.title}'")
            
            # Check if this task exists in Google Tasks
            if local_task.id in google_task_dict:
                # Task exists in Google, check if it needs updating
                google_task = google_task_dict[local_task.id]
                logger.debug(f"Task '{local_task.title}' exists in Google with same ID")
                
                # Update the task in Google if it has changed
                local_modified = _normalize_datetime(local_task.modified_at) or _normalize_datetime(datetime.min)
                google_modified = _normalize_datetime(google_task.modified_at) or _normalize_datetime(datetime.min)
                
                if local_modified > google_modified:
                    # Update task in Google
                    logger.info(f"Updating task '{local_task.title}' in Google (local is newer)")
                    try:
                        updated_task = self.google_client.update_task(local_task, tasklist_id)
                        if updated_task:
                            tasks_updated += 1
                            logger.debug(f"Updated task in Google: {local_task.title}")
                        else:
                            tasks_failed_auth += 1
                            logger.warning(f"Failed to update task in Google (possibly due to auth): {local_task.title}")
                    except Exception as e:
                        tasks_failed_auth += 1
                        logger.error(f"Exception while updating task '{local_task.title}': {e}")
                else:
                    logger.debug(f"Not updating task '{local_task.title}' - Google version is newer or equal")
            else:
                # Task doesn't exist in Google, check by signature
                print(f"Task '{local_task.title}' does not exist in Google by ID, checking by signature")
                logger.debug(f"Local signature: {local_signature}")
                logger.debug(f"Is local signature in google_signature_to_task? {local_signature in google_signature_to_task}")
                if local_signature in google_signature_to_task:
                    # Task exists in Google with different ID, update it
                    google_task = google_signature_to_task[local_signature]
                    logger.info(f"Task '{local_task.title}' exists in Google with different ID ({google_task.id}), updating")
                    # Update the local task ID to match Google
                    local_task.id = google_task.id
                    # Update task in Google
                    try:
                        updated_task = self.google_client.update_task(local_task, google_task.tasklist_id)
                        if updated_task:
                            tasks_updated += 1
                            logger.debug(f"Updated task in Google (ID sync): {local_task.title}")
                        else:
                            tasks_failed_auth += 1
                            logger.warning(f"Failed to update task in Google (ID sync, possibly due to auth): {local_task.title}")
                    except Exception as e:
                        tasks_failed_auth += 1
                        logger.error(f"Exception while updating task '{local_task.title}' (ID sync): {e}")
                else:
                    # Completely new task, create it in Google
                    logger.debug(f"Task '{local_task.title}' does not exist in Google, checking for duplicates before creation")
                    # Set the tasklist_id for the new task
                    local_task.tasklist_id = tasklist_id
                    
                    # Check if this task already exists to prevent duplicates
                    task_signature = create_task_signature(
                        title=local_task.title or "",
                        description=local_task.description or "",
                        due_date=local_task.due,
                        status=local_task.status,
                        notes=local_task.notes or ""
                    )
                    
                    logger.debug(f"Checking if task '{local_task.title}' already exists by signature")
                    logger.debug(f"Task signature: {task_signature}")
                    logger.debug(f"Is task signature in existing_signatures? {task_signature in existing_signatures}")
                    
                    # Additional duplicate check using the existing signatures
                    if task_signature in existing_signatures:
                        tasks_skipped += 1
                        logger.info(f"Task '{local_task.title}' already exists in Google Tasks (based on existing signatures). Skipping creation.")
                        logger.debug(f"Skipping creation of task '{local_task.title}' as it already exists")
                    else:
                        # Check if we can create the task safely (no auth issues)
                        if not self._can_safely_create_task(tasklist_id, task_signature, local_task.title):
                            tasks_failed_auth += 1
                            tasks_duplicate_check_failed += 1
                            logger.error(f"CRITICAL: Cannot safely create task '{local_task.title}'. "
                                       f"ABORTING task creation to prevent duplicates.")
                            continue
                            
                        # ONLY create task if all checks pass
                        # Add one final connection check before creating the task
                        if not self.google_client.connect():
                            tasks_failed_auth += 1
                            tasks_duplicate_check_failed += 1
                            logger.error(f"CRITICAL: Connection failed right before task creation for '{local_task.title}'. "
                                       f"ABORTING task creation to prevent duplicates.")
                            continue
                            
                        logger.debug(f"Creating new task: {local_task.title}")
                        new_task = self.google_client.create_task(local_task)
                        if new_task:
                            tasks_created += 1
                            logger.debug(f"Created new task in Google: {local_task.title}")
                        else:
                            tasks_failed_auth += 1
                            logger.warning(f"Failed to create task in Google (possibly due to auth): {local_task.title}")
        
        logger.info(f"Push operation summary - Created: {tasks_created}, Updated: {tasks_updated}, Skipped: {tasks_skipped}, "
                   f"Auth Failed: {tasks_failed_auth}, Duplicate Check Failed: {tasks_duplicate_check_failed}")
        # Return all Google tasks (they are now up to date)
        return google_tasks
    
    def _can_safely_create_task(self, tasklist_id: str, task_signature: str, task_title: str) -> bool:
        """
        Verify that we can safely create a task without causing duplicates due to auth issues.
        
        Returns:
            bool: True if it's safe to create the task, False otherwise
        """
        # First check basic connection
        if not self.google_client.connect():
            logger.error(f"CRITICAL: Cannot connect to Google Tasks. ABORTING task creation for '{task_title}' to prevent duplicates.")
            return False
            
        # Check if authentication has failed previously
        if hasattr(self.google_client, '_auth_failed') and self.google_client._auth_failed:
            logger.error(f"CRITICAL: Authentication has previously failed. ABORTING task creation for '{task_title}' to prevent duplicates.")
            return False
            
        # If we're using the optimized approach with a temporary database, 
        # we can skip the additional API calls and rely on the data we already loaded
        if hasattr(self, '_temp_db_path') and self._temp_db_path:
            logger.debug(f"Using temporary database for safety check of task '{task_title}'")
            try:
                # Check if task already exists in our temporary database
                conn = sqlite3.connect(self._temp_db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM temp_google_tasks 
                    WHERE signature = ? AND tasklist_id = ?
                ''', (task_signature, tasklist_id))
                
                count = cursor.fetchone()[0]
                conn.close()
                
                if count > 0:
                    logger.info(f"Task '{task_title}' already exists in Google Tasks (from temp database). Skipping creation.")
                    return False
                    
                # If we have the temporary database, we consider this safe
                # since we've already loaded all the tasks
                logger.debug(f"Task '{task_title}' does not exist in temporary database. Proceeding with creation.")
                return True
            except Exception as e:
                logger.warning(f"Failed to check temporary database for task '{task_title}': {e}")
                # Even if database check fails, we still have the data we loaded earlier
                # so we don't need to make additional API calls
                logger.debug(f"Falling back to previously loaded data for task '{task_title}' safety check")
                return True
        
        # Fall back to API calls for safety check (should not happen with our new approach)
        logger.warning(f"Falling back to API calls for safety check of task '{task_title}' - this should not happen with the new approach")
        try:
            # Verify API access by listing tasklists
            test_tasklists = self.google_client.list_tasklists()
            if not test_tasklists:
                logger.error(f"CRITICAL: Cannot retrieve tasklists from Google Tasks. "
                            f"ABORTING task creation for '{task_title}' to prevent duplicates.")
                return False
                
            # Verify access to specific tasklist
            test_tasks = self.google_client.list_tasks(
                tasklist_id=tasklist_id,
                show_completed=True,
                show_hidden=True,
                show_deleted=False
            )
            
            # Final check for duplicates in current Google data
            current_google_tasks = self.google_client.list_tasks(
                tasklist_id=tasklist_id,
                show_completed=True,
                show_hidden=True,
                show_deleted=False
            )
            
            current_google_signatures = set()
            for task in current_google_tasks:
                signature = create_task_signature(
                    title=task.title or "",
                    description=task.description or "",
                    due_date=task.due,
                    status=task.status,
                    notes=task.notes or ""
                )
                current_google_signatures.add(signature)
            
            if task_signature in current_google_signatures:
                logger.info(f"Task '{task_title}' already exists in Google Tasks (reconfirmed). Skipping creation.")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"CRITICAL: Cannot verify Google Tasks API access. "
                        f"ABORTING task creation for '{task_title}' to prevent duplicates: {e}")
            # Mark authentication as failed if we get an auth error
            if 'invalid_grant' in str(e):
                if hasattr(self.google_client, '_auth_failed'):
                    self.google_client._auth_failed = True
                logger.error(f"CRITICAL: Authentication failed during safety check. "
                            f"Marking auth as failed to prevent duplicates for '{task_title}'.")
            return False
    
    def _pull_google_tasks(self, local_tasks: List[Task], google_tasks: List[Task],
                          tasklist_id_to_title: Dict[str, str]) -> List[Task]:
        """
        Pull Google tasks to local storage.
        
        Args:
            local_tasks: List of local tasks
            google_tasks: List of Google tasks
            tasklist_id_to_title: Mapping of tasklist IDs to titles
            
        Returns:
            List[Task]: List of tasks after pull operation
        """
        # Create mappings for easier lookup
        local_task_dict = {task.id: task for task in local_tasks}
        local_signature_to_task = {}
        
        for task in local_tasks:
            signature = create_task_signature(
                title=task.title or "",
                description=task.description or "",
                due_date=task.due,
                status=task.status,
                notes=task.notes or ""
            )
            local_signature_to_task[signature] = task
        
        logger.debug(f"Created local task mappings: {len(local_task_dict)} by ID, {len(local_signature_to_task)} by signature")
        
        # Start with all local tasks
        synced_tasks = local_tasks.copy()
        tasks_downloaded = 0
        tasks_updated = 0
        tasks_skipped = 0
        
        # Process Google tasks - download new tasks from Google
        for google_task in google_tasks:
            google_signature = create_task_signature(
                title=google_task.title or "",
                description=google_task.description or "",
                due_date=google_task.due,
                status=google_task.status
            )
            
            logger.debug(f"Processing Google task '{google_task.title}' (ID: {google_task.id}) with signature: {google_signature}")
            
            if google_task.id not in local_task_dict and google_signature not in local_signature_to_task:
                # This is a new task from Google, add it to local tasks
                synced_tasks.append(google_task)
                tasks_downloaded += 1
                logger.debug(f"Downloaded new task from Google: {google_task.title}")
            elif google_task.id in local_task_dict:
                # Task exists locally, check if Google version is newer
                local_task = local_task_dict[google_task.id]
                local_modified = _normalize_datetime(local_task.modified_at) or _normalize_datetime(datetime.min)
                google_modified = _normalize_datetime(google_task.modified_at) or _normalize_datetime(datetime.min)
                
                if google_modified > local_modified:
                    # Google version is newer, update local task
                    # Replace the local task with the Google task in our list
                    synced_tasks = [task if task.id != google_task.id else google_task for task in synced_tasks]
                    tasks_updated += 1
                    logger.debug(f"Updated local task from Google: {google_task.title}")
                else:
                    tasks_skipped += 1
                    logger.debug(f"Not updating local task '{google_task.title}' - local version is newer or equal")
            elif google_signature in local_signature_to_task:
                # Task exists locally with different ID, check which is newer
                local_task = local_signature_to_task[google_signature]
                local_modified = _normalize_datetime(local_task.modified_at) or _normalize_datetime(datetime.min)
                google_modified = _normalize_datetime(google_task.modified_at) or _normalize_datetime(datetime.min)
                
                if google_modified > local_modified:
                    # Google version is newer, update local task
                    # Replace the local task with the Google task in our list
                    synced_tasks = [task if task.id != local_task.id else google_task for task in synced_tasks]
                    # Update the ID to match Google
                    for task in synced_tasks:
                        if task.id == local_task.id:
                            task.id = google_task.id
                            task.tasklist_id = google_task.tasklist_id
                            break
                    tasks_updated += 1
                    logger.debug(f"Updated local task from Google (ID sync): {google_task.title}")
                else:
                    tasks_skipped += 1
                    logger.debug(f"Not updating local task '{google_task.title}' (ID sync) - local version is newer or equal")
            # Additional check for edge cases
            elif google_task.id not in local_task_dict and google_signature in local_signature_to_task:
                # This is a duplicate task with different ID, skip it
                tasks_skipped += 1
                logger.info(f"Skipping duplicate task from Google: {google_task.title}")
        
        logger.info(f"Pull operation summary - Downloaded: {tasks_downloaded}, Updated: {tasks_updated}, Skipped: {tasks_skipped}")
        
        # Remove duplicates from synced_tasks based on signatures
        unique_tasks = self._remove_duplicates_from_list(synced_tasks)
        
        return unique_tasks
    
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
    
    def _create_temp_database(self) -> str:
        """
        Create a temporary database for storing Google Tasks during sync.
        
        Returns:
            str: Path to the temporary database file
        """
        # Create a temporary database file
        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db', prefix='gtasks_sync_')
        os.close(temp_db_fd)  # Close the file descriptor, we'll use the path
        
        # Create the database schema
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Create table for Google Tasks
        cursor.execute('''
            CREATE TABLE temp_google_tasks (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                due TEXT,
                priority TEXT,
                status TEXT,
                project TEXT,
                tags TEXT,
                notes TEXT,
                dependencies TEXT,
                recurrence_rule TEXT,
                created_at TEXT,
                modified_at TEXT,
                tasklist_id TEXT,
                signature TEXT
            )
        ''')
        
        # Create indexes for faster lookups
        cursor.execute('CREATE INDEX idx_signature ON temp_google_tasks(signature)')
        cursor.execute('CREATE INDEX idx_tasklist ON temp_google_tasks(tasklist_id)')
        cursor.execute('CREATE INDEX idx_modified_at ON temp_google_tasks(modified_at)')
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Created temporary database at {temp_db_path}")
        return temp_db_path
    
    def _load_google_tasks_to_temp_db(self, temp_db_path: str) -> int:
        """
        Load all Google Tasks into the temporary database.
        
        Args:
            temp_db_path: Path to the temporary database file
            
        Returns:
            int: Number of tasks loaded
        """
        logger.info("Loading Google Tasks into temporary database")
        
        # Connect to the temporary database
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Get all tasklists
        tasklists = self.google_client.list_tasklists()
        if not tasklists:
            logger.warning("No tasklists found in Google Tasks")
            conn.close()
            return 0
        
        task_count = 0
        
        # Load tasks from each tasklist
        for tasklist in tasklists:
            tasklist_id = tasklist['id']
            tasklist_title = tasklist['title']
            
            logger.debug(f"Loading tasks from tasklist: {tasklist_title}")
            
            # Get all tasks from this tasklist
            tasks = self.google_client.list_tasks(
                tasklist_id=tasklist_id,
                show_completed=True,
                show_hidden=True,
                show_deleted=False
            )
            
            if not tasks:
                logger.debug(f"No tasks found in tasklist: {tasklist_title}")
                continue
            
            # Insert tasks into temporary database
            for task in tasks:
                # Create task signature for duplicate detection
                signature = self._create_task_signature(
                    title=task.title or "",
                    description=task.description or "",
                    due_date=task.due,
                    status=task.status
                )
                
                # Convert task to dictionary for database insertion
                task_dict = {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'due': task.due.isoformat() if task.due else None,
                    'priority': task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                    'status': task.status.value if hasattr(task.status, 'value') else str(task.status),
                    'project': task.project,
                    'tags': json.dumps(task.tags) if task.tags else None,
                    'notes': task.notes,
                    'dependencies': json.dumps(task.dependencies) if task.dependencies else None,
                    'recurrence_rule': task.recurrence_rule,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'modified_at': task.modified_at.isoformat() if task.modified_at else None,
                    'tasklist_id': tasklist_id,
                    'signature': signature
                }
                
                # Insert task into database
                cursor.execute('''
                    INSERT OR REPLACE INTO temp_google_tasks 
                    (id, title, description, due, priority, status, project, tags, notes, 
                     dependencies, recurrence_rule, created_at, modified_at, tasklist_id, signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_dict['id'], task_dict['title'], task_dict['description'], task_dict['due'],
                    task_dict['priority'], task_dict['status'], task_dict['project'], task_dict['tags'],
                    task_dict['notes'], task_dict['dependencies'], task_dict['recurrence_rule'],
                    task_dict['created_at'], task_dict['modified_at'], task_dict['tasklist_id'], task_dict['signature']
                ))
            
            task_count += len(tasks)
            logger.debug(f"Loaded {len(tasks)} tasks from tasklist: {tasklist_title}")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logger.info(f"Loaded {task_count} Google Tasks into temporary database")
        return task_count
    
    def _create_task_signature(self, title: str, description: str, due_date: Optional[datetime], status: str) -> str:
        """
        Create a signature for a task to detect duplicates.
        
        Args:
            title: Task title
            description: Task description
            due_date: Task due date
            status: Task status
            
        Returns:
            str: MD5 hash signature of the task
        """
        # Normalize due_date for signature
        due_str = ""
        if due_date:
            if isinstance(due_date, str):
                due_str = due_date
            else:
                due_str = due_date.isoformat()
        
        # Combine description and notes for signature since they are the same in Google Tasks
        # This handles the case where a task might have content in either field
        combined_description = ""
        if description:
            combined_description = description
        # We don't have access to notes here, but in the calling code we should combine them
        
        # Create signature string
        signature_string = f"{title}|{description}|{due_str}|{status}"
        
        # Create MD5 hash
        return hashlib.md5(signature_string.encode()).hexdigest()
    
    def _batch_create_tasks(self, tasks: List) -> Tuple[List, int, int]:
        """
        Create multiple tasks in batch.
        
        Args:
            tasks: List of tasks to create
            
        Returns:
            Tuple[List, int, int]: (created_tasks, success_count, failure_count)
        """
        created_tasks = []
        success_count = 0
        failure_count = 0
        
        logger.info(f"Creating {len(tasks)} tasks in batch")
        
        for task in tasks:
            try:
                # Check if we can still create tasks (authentication check)
                if not self.google_client.connect():
                    logger.error("Lost connection to Google Tasks. Aborting batch creation.")
                    failure_count += 1
                    continue
                    
                created_task = self.google_client.create_task(task)
                if created_task:
                    created_tasks.append(created_task)
                    success_count += 1
                    logger.debug(f"Successfully created task: {task.title}")
                else:
                    failure_count += 1
                    logger.warning(f"Failed to create task: {task.title}")
            except Exception as e:
                failure_count += 1
                logger.error(f"Exception while creating task '{task.title}': {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"Batch creation completed: {success_count} succeeded, {failure_count} failed")
        return created_tasks, success_count, failure_count
    
    def _batch_update_tasks(self, tasks: List) -> Tuple[List, int, int]:
        """
        Update multiple tasks in batch.
        
        Args:
            tasks: List of tasks to update
            
        Returns:
            Tuple[List, int, int]: (updated_tasks, success_count, failure_count)
        """
        updated_tasks = []
        success_count = 0
        failure_count = 0
        
        logger.info(f"Updating {len(tasks)} tasks in batch")
        
        for task in tasks:
            try:
                # Check if we can still update tasks (authentication check)
                if not self.google_client.connect():
                    logger.error("Lost connection to Google Tasks. Aborting batch update.")
                    failure_count += 1
                    continue
                    
                # For updates, we need the tasklist_id
                tasklist_id = getattr(task, 'tasklist_id', '@default')
                updated_task = self.google_client.update_task(task, tasklist_id)
                if updated_task:
                    updated_tasks.append(updated_task)
                    success_count += 1
                    logger.debug(f"Successfully updated task: {task.title}")
                else:
                    failure_count += 1
                    logger.warning(f"Failed to update task: {task.title}")
            except Exception as e:
                failure_count += 1
                logger.error(f"Exception while updating task '{task.title}': {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"Batch update completed: {success_count} succeeded, {failure_count} failed")
        return updated_tasks, success_count, failure_count
