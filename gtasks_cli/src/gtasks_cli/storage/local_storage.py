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
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the LocalStorage.
        
        Args:
            storage_path: Path to storage file. If None, uses default location.
        """
        if storage_path is None:
            # Default storage location
            storage_dir = Path.home() / '.gtasks'
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = storage_dir / 'tasks.json'
        else:
            self.storage_path = Path(storage_path)
            
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