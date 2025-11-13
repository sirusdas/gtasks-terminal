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
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the SQLiteStorage.
        
        Args:
            storage_path: Path to SQLite database file. If None, uses default location.
        """
        if storage_path is None:
            # Default storage location
            storage_dir = Path.home() / '.gtasks'
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = storage_dir / 'tasks.db'
        else:
            self.storage_path = Path(storage_path)
            
        logger.debug(f"SQLiteStorage initialized with file: {self.storage_path}")
        self._initialize_database()
    
    def _initialize_database(self) -> None:
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
                
                # Create lists table for task list mappings
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_lists (
                        task_id TEXT PRIMARY KEY,
                        list_name TEXT NOT NULL
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
                    
                    # Serialize list fields as JSON
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
                        task.get('due').isoformat() if task.get('due') else None,
                        task.get('priority'),
                        task.get('status'),
                        task.get('project'),
                        tags_json,
                        task.get('notes'),
                        dependencies_json,
                        task.get('recurrence_rule'),
                        task.get('created_at').isoformat() if task.get('created_at') else None,
                        task.get('modified_at').isoformat() if task.get('modified_at') else None,
                        task.get('completed_at').isoformat() if task.get('completed_at') else None,
                        task.get('estimated_duration'),
                        task.get('actual_duration'),
                        task.get('is_recurring'),
                        task.get('recurring_task_id'),
                        task.get('tasklist_id')
                    ))
                
                conn.commit()
                logger.debug(f"Saved {len(tasks)} tasks to database")
        except sqlite3.Error as e:
            logger.error(f"Error saving tasks to database: {e}")
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """
        Load tasks from SQLite database.
        
        Returns:
            List[Dict[str, Any]]: List of task dictionaries
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM tasks')
                rows = cursor.fetchall()
                
                tasks = []
                for row in rows:
                    # Convert row to dictionary
                    task = dict(row)
                    
                    # Deserialize JSON fields
                    if task['tags']:
                        try:
                            task['tags'] = json.loads(task['tags'])
                        except (json.JSONDecodeError, TypeError):
                            task['tags'] = []
                    
                    if task['dependencies']:
                        try:
                            task['dependencies'] = json.loads(task['dependencies'])
                        except (json.JSONDecodeError, TypeError):
                            task['dependencies'] = []
                    
                    # Convert datetime strings back to datetime objects
                    for date_field in ['due', 'created_at', 'modified_at', 'completed_at']:
                        if task[date_field]:
                            try:
                                task[date_field] = datetime.fromisoformat(task[date_field])
                            except ValueError:
                                task[date_field] = None
                    
                    tasks.append(task)
                
                logger.debug(f"Loaded {len(tasks)} tasks from database")
                return tasks
        except sqlite3.Error as e:
            logger.error(f"Error loading tasks from database: {e}")
            return []
    
    def save_list_mapping(self, list_mapping: Dict[str, str]) -> None:
        """
        Save task list mapping to SQLite database.
        
        Args:
            list_mapping: Dictionary mapping task IDs to list names
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                
                for task_id, list_name in list_mapping.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO task_lists (task_id, list_name)
                        VALUES (?, ?)
                    ''', (task_id, list_name))
                
                conn.commit()
                logger.debug(f"Saved {len(list_mapping)} list mappings to database")
        except sqlite3.Error as e:
            logger.error(f"Error saving list mapping to database: {e}")
    
    def load_list_mapping(self) -> Dict[str, str]:
        """
        Load task list mapping from SQLite database.
        
        Returns:
            Dict[str, str]: Dictionary mapping task IDs to list names
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT task_id, list_name FROM task_lists')
                rows = cursor.fetchall()
                
                list_mapping = {row['task_id']: row['list_name'] for row in rows}
                logger.debug(f"Loaded {len(list_mapping)} list mappings from database")
                return list_mapping
        except sqlite3.Error as e:
            logger.error(f"Error loading list mapping from database: {e}")
            return {}
    
    def query_tasks(self, list_name: Optional[str] = None, status: Optional[str] = None, 
                   search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query tasks with filters - demonstrates SQLite's querying capabilities.
        
        Args:
            list_name: Filter by list name
            status: Filter by task status
            search: Search in title or description
            
        Returns:
            List[Dict[str, Any]]: List of matching task dictionaries
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build query dynamically
                query = "SELECT t.* FROM tasks t"
                conditions = []
                params = []
                
                # Join with task_lists if filtering by list name
                if list_name:
                    query += " LEFT JOIN task_lists tl ON t.id = tl.task_id"
                    conditions.append("tl.list_name LIKE ?")
                    params.append(f"%{list_name}%")
                
                # Add status filter
                if status:
                    conditions.append("t.status = ?")
                    params.append(status)
                
                # Add search filter
                if search:
                    conditions.append("(t.title LIKE ? OR t.description LIKE ?)")
                    params.extend([f"%{search}%", f"%{search}%"])
                
                # Complete query
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY t.due ASC, t.created_at DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                tasks = []
                for row in rows:
                    # Convert row to dictionary
                    task = dict(row)
                    
                    # Deserialize JSON fields
                    if task['tags']:
                        try:
                            task['tags'] = json.loads(task['tags'])
                        except (json.JSONDecodeError, TypeError):
                            task['tags'] = []
                    
                    if task['dependencies']:
                        try:
                            task['dependencies'] = json.loads(task['dependencies'])
                        except (json.JSONDecodeError, TypeError):
                            task['dependencies'] = []
                    
                    # Convert datetime strings back to datetime objects
                    for date_field in ['due', 'created_at', 'modified_at', 'completed_at']:
                        if task[date_field]:
                            try:
                                task[date_field] = datetime.fromisoformat(task[date_field])
                            except ValueError:
                                task[date_field] = None
                    
                    tasks.append(task)
                
                logger.debug(f"Queried {len(tasks)} tasks from database")
                return tasks
        except sqlite3.Error as e:
            logger.error(f"Error querying tasks from database: {e}")
            return []