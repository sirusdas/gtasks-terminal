#!/usr/bin/env python3
"""
Debug script for LocalStorage.
"""

import sys
import os

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gtasks_cli.storage.local_storage import LocalStorage
from datetime import datetime
import uuid


def test_storage():
    """Test LocalStorage functionality."""
    print("Testing LocalStorage...")
    
    # Create storage instance
    storage = LocalStorage()
    print(f"Storage path: {storage.storage_path}")
    
    # Test saving tasks
    tasks = [
        {
            "id": str(uuid.uuid4()),
            "title": "Test Task",
            "description": "Test description",
            "due": datetime.now(),
            "priority": "high",
            "status": "pending",
            "project": "Test Project",
            "tags": ["test", "debug"],
            "tasklist_id": "default",
            "position": 0,
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        }
    ]
    
    print("Saving tasks...")
    storage.save_tasks(tasks)
    
    # Check if file exists
    print(f"File exists: {storage.storage_path.exists()}")
    
    # Test loading tasks
    print("Loading tasks...")
    loaded_tasks = storage.load_tasks()
    print(f"Loaded {len(loaded_tasks)} tasks")
    
    if loaded_tasks:
        print(f"First task: {loaded_tasks[0]['title']}")


if __name__ == "__main__":
    test_storage()