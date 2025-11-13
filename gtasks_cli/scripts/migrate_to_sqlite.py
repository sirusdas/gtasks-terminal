"""
Migration script to convert from JSON file storage to SQLite database.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import our modules
from gtasks_cli.storage.local_storage import LocalStorage
from gtasks_cli.storage.sqlite_storage import SQLiteStorage
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


def migrate():
    """Migrate data from JSON files to SQLite database."""
    print("Starting migration from JSON to SQLite...")
    
    # Initialize storages
    json_storage = LocalStorage()
    sqlite_storage = SQLiteStorage()
    
    # Backup existing data
    backup_dir = Path.home() / '.gtasks' / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup tasks.json
    if json_storage.storage_path.exists():
        backup_path = backup_dir / f"tasks_backup_{timestamp}.json"
        with open(json_storage.storage_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Backed up tasks.json to {backup_path}")
    
    # Backup lists.json
    if json_storage.lists_path.exists():
        backup_path = backup_dir / f"lists_backup_{timestamp}.json"
        with open(json_storage.lists_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Backed up lists.json to {backup_path}")
    
    # Load data from JSON
    tasks = json_storage.load_tasks()
    list_mapping = json_storage.load_list_mapping()
    
    logger.info(f"Loaded {len(tasks)} tasks and {len(list_mapping)} list mappings from JSON")
    
    # Migrate tasks
    if tasks:
        sqlite_storage.save_tasks(tasks)
        logger.info(f"Migrated {len(tasks)} tasks to SQLite")
    
    # Migrate list mappings
    if list_mapping:
        sqlite_storage.save_list_mapping(list_mapping)
        logger.info(f"Migrated {len(list_mapping)} list mappings to SQLite")
    
    # Create confirmation file
    migration_log = backup_dir / f"migration_log_{timestamp}.txt"
    with open(migration_log, 'w') as f:
        f.write(f"Migration completed at {datetime.now().isoformat()}")
        f.write(f"\nTasks migrated: {len(tasks)}")
        f.write(f"\nList mappings migrated: {len(list_mapping)}")
        f.write(f"\nBackup directory: {backup_dir}")
    
    print("Migration completed successfully!")
    print(f"Backups saved to: {backup_dir}")
    print(f"Migration log: {migration_log}")
    
    # Verify migration
    verify_migration(sqlite_storage, len(tasks), len(list_mapping))


def verify_migration(sqlite_storage, expected_tasks, expected_mappings):
    """Verify that migration was successful."""
    print("\nVerifying migration...")
    
    # Check task count
    migrated_tasks = sqlite_storage.load_tasks()
    if len(migrated_tasks) == expected_tasks:
        print(f"✓ Task count verified: {len(migrated_tasks)} tasks")
    else:
        print(f"✗ Task count mismatch: expected {expected_tasks}, got {len(migrated_tasks)}")
    
    # Check list mapping count
    migrated_mappings = sqlite_storage.load_list_mapping()
    if len(migrated_mappings) == expected_mappings:
        print(f"✓ List mapping count verified: {len(migrated_mappings)} mappings")
    else:
        print(f"✗ List mapping count mismatch: expected {expected_mappings}, got {len(migrated_mappings)}")
    
    # Check a few random tasks for data integrity
    if migrated_tasks:
        sample_task = migrated_tasks[0]
        print(f"\nSample task verification:")
        print(f"  ID: {sample_task.get('id')}")
        print(f"  Title: {sample_task.get('title')}")
        print(f"  Status: {sample_task.get('status')}")
        if sample_task.get('due'):
            print(f"  Due: {sample_task.get('due').isoformat()}")
    
    print("\nMigration verification complete!")

if __name__ == "__main__":
    migrate()