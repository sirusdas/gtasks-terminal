"""
SQLite storage implementation for the Google Tasks CLI application.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


class SQLiteStorage:
    """SQLite-based storage for tasks."""
    
    def __init__(self, storage_path: str = None, account_name: str = None):
        """
        Initialize the SQLiteStorage.
        
        Args:
            storage_path: Path to SQLite database file. If None, uses default location.
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
            self.storage_path = storage_dir / 'tasks.db'
            logger.info(f"Using SQLite storage at: {self.storage_path} for account: {account_name}")
        elif config_dir_env:
            # Use custom config directory but default database name
            storage_dir = Path(config_dir_env)
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = storage_dir / 'tasks.db'
            logger.info(f"Using SQLite storage at: {self.storage_path} (custom config directory)")
        elif storage_path is None:
            # Default storage location
            storage_dir = Path.home() / '.gtasks'
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = storage_dir / 'tasks.db'
            logger.info(f"Using SQLite storage at: {self.storage_path} (default location)")
        else:
            self.storage_path = Path(storage_path)
            logger.info(f"Using SQLite storage at: {self.storage_path} (custom path)")
            
        # Initialize database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                
                # Create tasks table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        due DATETIME,
                        priority TEXT,
                        status TEXT,
                        project TEXT,
                        tags TEXT,  -- JSON serialized list
                        notes TEXT,
                        dependencies TEXT,  -- JSON serialized list
                        recurrence_rule TEXT,
                        created_at DATETIME,
                        modified_at DATETIME,
                        completed_at DATETIME,
                        estimated_duration INTEGER,
                        actual_duration INTEGER,
                        is_recurring BOOLEAN,
                        recurring_task_id TEXT,
                        tasklist_id TEXT
                    )
                ''')
                
                # Create lists table for task list mappings with foreign key constraint
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_lists (
                        task_id TEXT PRIMARY KEY,
                        list_name TEXT NOT NULL,
                        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
                    )
                ''')
                
                # Create indexes for better query performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_list ON task_lists(list_name)')
                
                conn.commit()
                logger.debug("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
    
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Save tasks to SQLite database.
        
        Args:
            tasks: List of task dictionaries to save
        """
        try:
            logger.debug(f"Saving {len(tasks)} tasks to database")
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                
                for task in tasks:
                    # Log the task being saved
                    logger.debug(f"Saving task: {task.get('id')} - {task.get('title')} - {task.get('status')}")
                    
                    # Serialize lists to JSON strings
                    tags_json = json.dumps(task.get('tags', []))
                    dependencies_json = json.dumps(task.get('dependencies', []))
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO tasks (
                            id, title, description, due, priority, status, project,
                            tags, notes, dependencies, recurrence_rule, created_at,
                            modified_at, completed_at, estimated_duration, actual_duration,
                            is_recurring, recurring_task_id, tasklist_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        task.get('id'),
                        task.get('title'),
                        task.get('description'),
                        task.get('due'),
                        task.get('priority', 'medium'),
                        task.get('status', 'pending'),
                        task.get('project'),
                        tags_json,
                        task.get('notes'),
                        dependencies_json,
                        task.get('recurrence_rule'),
                        task.get('created_at'),
                        task.get('modified_at'),
                        task.get('completed_at'),
                        task.get('estimated_duration'),
                        task.get('actual_duration'),
                        task.get('is_recurring', False),
                        task.get('recurring_task_id'),
                        task.get('tasklist_id')
                    ))
                    
                    # Save list mapping if available
                    if 'list_name' in task:
                        cursor.execute('''
                            INSERT OR REPLACE INTO task_lists (task_id, list_name)
                            VALUES (?, ?)
                        ''', (task.get('id'), task.get('list_name')))
                
                conn.commit()
                logger.debug(f"Successfully saved {len(tasks)} tasks to database")
        except sqlite3.Error as e:
            logger.error(f"Error saving tasks to database: {e}")
            raise
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """
        Load tasks from SQLite database.
        
        Returns:
            List of task dictionaries
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        t.id, t.title, t.description, t.due, t.priority, t.status, t.project,
                        t.tags, t.notes, t.dependencies, t.recurrence_rule, t.created_at,
                        t.modified_at, t.completed_at, t.estimated_duration, t.actual_duration,
                        t.is_recurring, t.recurring_task_id, t.tasklist_id,
                        l.list_name
                    FROM tasks t
                    LEFT JOIN task_lists l ON t.id = l.task_id
                ''')
                
                rows = cursor.fetchall()
                logger.debug(f"Loaded {len(rows)} rows from database")
                tasks = []
                
                for row in rows:
                    # Parse JSON strings back to lists
                    tags = json.loads(row[7]) if row[7] else []
                    dependencies = json.loads(row[9]) if row[9] else []
                    
                    task = {
                        'id': row[0],
                        'title': row[1],
                        'description': row[2],
                        'due': row[3],
                        'priority': row[4],
                        'status': row[5],
                        'project': row[6],
                        'tags': tags,
                        'notes': row[8],
                        'dependencies': dependencies,
                        'recurrence_rule': row[10],
                        'created_at': row[11],
                        'modified_at': row[12],
                        'completed_at': row[13],
                        'estimated_duration': row[14],
                        'actual_duration': row[15],
                        'is_recurring': row[16],
                        'recurring_task_id': row[17],
                        'tasklist_id': row[18],
                        'list_name': row[19] if len(row) > 19 else None
                    }
                    tasks.append(task)
                
                # Load list mappings
                cursor.execute('SELECT task_id, list_name FROM task_lists')
                list_mappings = {row[0]: row[1] for row in cursor.fetchall()}
                
                # List name is already included from the JOIN in the main query
                
                logger.debug(f"Loaded {len(tasks)} tasks from database")
                return tasks
        except sqlite3.Error as e:
            logger.error(f"Error loading tasks from database: {e}")
            return []
    
    def load_list_mapping(self) -> Dict[str, str]:
        """
        Load task list mappings from database.
        
        Returns:
            Dictionary mapping task IDs to list names
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT task_id, list_name FROM task_lists')
                mappings = {row[0]: row[1] for row in cursor.fetchall()}
                logger.debug(f"Loaded {len(mappings)} list mappings from database")
                return mappings
        except sqlite3.Error as e:
            logger.error(f"Error loading list mappings from database: {e}")
            return {}
    
    def save_list_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Save task list mappings to database.
        
        Args:
            mapping: Dictionary mapping task IDs to list names
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                
                for task_id, list_name in mapping.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO task_lists (task_id, list_name)
                        VALUES (?, ?)
                    ''', (task_id, list_name))
                
                conn.commit()
                logger.debug(f"Saved {len(mapping)} list mappings to database")
        except sqlite3.Error as e:
            logger.error(f"Error saving list mappings to database: {e}")
            raise
    
    def clear_tasks(self) -> None:
        """Clear all tasks from the database."""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks')
                cursor.execute('DELETE FROM task_lists')
                conn.commit()
                logger.debug("Cleared all tasks from database")
        except sqlite3.Error as e:
            logger.error(f"Error clearing tasks from database: {e}")
            raise

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from the database.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                # Cascade delete should handle task_lists, but let's be safe
                cursor.execute('DELETE FROM task_lists WHERE task_id = ?', (task_id,))
                conn.commit()
                logger.debug(f"Deleted task {task_id} from database")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting task {task_id} from database: {e}")
            return False