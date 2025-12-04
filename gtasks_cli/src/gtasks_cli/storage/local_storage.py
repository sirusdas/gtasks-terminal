"""
Local storage implementation for the Google Tasks CLI application.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


class LocalStorage:
    """Simple file-based local storage for tasks."""
    
    def __init__(self, storage_path: str = None, account_name: str = None):
        """
        Initialize the LocalStorage.
        
        Args:
            storage_path: Path to storage file. If None, uses default location.
            account_name: Name of the account for multi-account support
        """
        # Check for GTASKS_CONFIG_DIR environment variable for multi-account support
        config_dir_env = os.environ.get('GTASKS_CONFIG_DIR')
        
        if account_name:
            # For multi-account support, use account-specific paths
            if config_dir_env:
                storage_dir = Path(config_dir_env)
            else:
                storage_dir = Path.home() / '.gtasks' / account_name
            
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = storage_dir / 'tasks.json'
            self.lists_path = storage_dir / 'lists.json'
            logger.info(f"Using JSON storage at: {self.storage_path} for account: {account_name}")
        elif config_dir_env:
            # Use custom config directory but default filenames
            storage_dir = Path(config_dir_env)
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = storage_dir / 'tasks.json'
            self.lists_path = storage_dir / 'lists.json'
            logger.info(f"Using JSON storage at: {self.storage_path} (custom config directory)")
        elif storage_path is None:
            # Default storage location
            storage_dir = Path.home() / '.gtasks'
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = storage_dir / 'tasks.json'
            self.lists_path = storage_dir / 'lists.json'  # New file for list mappings
            logger.debug(f"LocalStorage initialized with file: {self.storage_path}")
        else:
            self.storage_path = Path(storage_path)
            self.lists_path = Path(storage_path).with_name('lists.json')
            logger.debug(f"LocalStorage initialized with file: {self.storage_path}")
    
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Save tasks to storage.
        
        Args:
            tasks: List of task dictionaries to save
        """
        try:
            logger.debug(f"Saving {len(tasks)} tasks to {self.storage_path}")
            
            # Convert datetime objects to strings for JSON serialization
            serializable_tasks = []
            for task in tasks:
                task_dict = task.copy()
                for key, value in task_dict.items():
                    if hasattr(value, 'isoformat'):  # datetime objects
                        task_dict[key] = value.isoformat()
                serializable_tasks.append(task_dict)
            
            with open(self.storage_path, 'w') as f:
                json.dump(serializable_tasks, f, indent=2)
            logger.debug(f"Saved {len(tasks)} tasks to {self.storage_path}")
        except Exception as e:
            logger.error(f"Error saving tasks to {self.storage_path}: {e}")
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """
        Load tasks from storage.
        
        Returns:
            List[Dict[str, Any]]: List of task dictionaries
        """
        if not self.storage_path.exists():
            logger.debug(f"Storage file {self.storage_path} does not exist, returning empty list")
            return []
            
        try:
            with open(self.storage_path, 'r') as f:
                tasks = json.load(f)
            
            # Convert datetime strings back to datetime objects
            from datetime import datetime
            for task in tasks:
                for key in ['due', 'created_at', 'modified_at', 'completed_at']:
                    if task.get(key):
                        try:
                            task[key] = datetime.fromisoformat(task[key])
                        except ValueError:
                            # If parsing fails, remove the field
                            task.pop(key, None)
            
            logger.debug(f"Loaded {len(tasks)} tasks from {self.storage_path}")
            return tasks
        except Exception as e:
            logger.error(f"Error loading tasks from {self.storage_path}: {e}")
            return []
    
    def save_list_mapping(self, list_mapping: Dict[str, str]) -> None:
        """
        Save task list mapping to storage.
        
        Args:
            list_mapping: Dictionary mapping task IDs to list names
        """
        try:
            logger.debug(f"Saving list mapping for {len(list_mapping)} tasks to {self.lists_path}")
            with open(self.lists_path, 'w') as f:
                json.dump(list_mapping, f, indent=2)
            logger.debug(f"Saved list mapping to {self.lists_path}")
        except Exception as e:
            logger.error(f"Error saving list mapping to {self.lists_path}: {e}")
    
    def load_list_mapping(self) -> Dict[str, str]:
        """
        Load task list mapping from storage.
        
        Returns:
            Dict[str, str]: Dictionary mapping task IDs to list names
        """
        if not self.lists_path.exists():
            logger.debug(f"List mapping file {self.lists_path} does not exist, returning empty dict")
            return {}
            
        try:
            with open(self.lists_path, 'r') as f:
                list_mapping = json.load(f)
            logger.debug(f"Loaded list mapping with {len(list_mapping)} entries from {self.lists_path}")
            return list_mapping
        except Exception as e:
            logger.error(f"Error loading list mapping from {self.lists_path}: {e}")
            return {}

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from storage.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            tasks = self.load_tasks()
            original_count = len(tasks)
            tasks = [t for t in tasks if t['id'] != task_id]
            
            if len(tasks) < original_count:
                self.save_tasks(tasks)
                
                # Also update list mapping
                list_mapping = self.load_list_mapping()
                if task_id in list_mapping:
                    del list_mapping[task_id]
                    self.save_list_mapping(list_mapping)
                    
                logger.debug(f"Deleted task {task_id} from storage")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting task {task_id} from storage: {e}")
            return False