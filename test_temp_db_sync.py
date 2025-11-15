#!/usr/bin/env python3
"""
Test script to verify the temporary database approach for advanced sync.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gtasks_cli', 'src'))

from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager
from gtasks_cli.storage.local_storage import LocalStorage
from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient

def test_temp_db_approach():
    """Test the temporary database approach for advanced sync."""
    print("Testing temporary database approach for advanced sync...")
    
    # Initialize components
    storage = LocalStorage()
    google_client = GoogleTasksClient()
    
    # Check if we can connect to Google Tasks
    if not google_client.connect():
        print("Failed to connect to Google Tasks. Please authenticate first.")
        return False
    
    # Create advanced sync manager
    sync_manager = AdvancedSyncManager(storage, google_client)
    
    # Test creating temporary database
    print("1. Creating temporary database...")
    try:
        temp_db_path = sync_manager._create_temp_database()
        print(f"   Created temporary database at: {temp_db_path}")
    except Exception as e:
        print(f"   Failed to create temporary database: {e}")
        return False
    
    # Test loading Google Tasks into temporary database
    print("2. Loading Google Tasks into temporary database...")
    try:
        task_count = sync_manager._load_google_tasks_to_temp_db(temp_db_path)
        print(f"   Loaded {task_count} tasks into temporary database")
    except Exception as e:
        print(f"   Failed to load Google Tasks: {e}")
        return False
    
    # Test creating task signature
    print("3. Testing task signature creation...")
    try:
        signature = sync_manager._create_task_signature(
            title="Test Task",
            description="This is a test task",
            due_date=None,
            status="pending"
        )
        print(f"   Created task signature: {signature}")
    except Exception as e:
        print(f"   Failed to create task signature: {e}")
        return False
    
    # Clean up temporary database
    print("4. Cleaning up...")
    try:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
            print(f"   Cleaned up temporary database: {temp_db_path}")
    except Exception as e:
        print(f"   Failed to clean up temporary database: {e}")
    
    print("Test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_temp_db_approach()
    if success:
        print("\n✓ Temporary database approach test passed!")
        sys.exit(0)
    else:
        print("\n✗ Temporary database approach test failed!")
        sys.exit(1)