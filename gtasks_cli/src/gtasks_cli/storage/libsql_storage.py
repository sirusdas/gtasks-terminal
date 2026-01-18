"""
LibSQL storage implementation for Turso/Remote database connection.
Provides bidirectional sync capabilities between local SQLite and remote Turso databases.

Uses the new `libsql` package (DB-API style) instead of deprecated `libsql-client`.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Try to import libsql, provide helpful error if not installed
try:
    import libsql
except ImportError:
    libsql = None
    libsql_import_error = "libsql package is required for remote database support. Install with: pip install libsql"

from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


class LibSQLStorage:
    """Storage implementation for Turso libSQL database using new DB-API style."""
    
    def __init__(self, url: str, auth_token: str = None, local_cache: str = None, account_name: str = None):
        """
        Initialize LibSQL storage.
        
        Args:
            url: Turso database URL (e.g., libsql://your-db.turso.io)
            auth_token: Authentication token (optional, uses GTASKS_TURSO_TOKEN env var or config file)
            local_cache: Optional local cache path for offline access
            account_name: Account name for multi-account support
        """
        if libsql is None:
            raise ImportError(libsql_import_error)
        
        self.url = url
        self.account_name = account_name
        
        # Token priority: 1) explicit param, 2) env var, 3) config file
        if auth_token:
            self.auth_token = auth_token
        elif os.getenv("GTASKS_TURSO_TOKEN"):
            self.auth_token = os.getenv("GTASKS_TURSO_TOKEN")
        else:
            # Try to load from config storage with account name
            from gtasks_cli.storage.sync_config_storage import SyncConfigStorage
            config_storage = SyncConfigStorage(account_name=account_name)
            self.auth_token = config_storage.get_turso_token(url)
        
        self.local_cache = local_cache
        self._conn = None
        self._init_connection()
    
    def _init_connection(self):
        """Initialize database connection."""
        try:
            logger.info(f"Connecting to: {self.url}")
            logger.debug(f"Auth token: {'***' + self.auth_token[-10:] if self.auth_token else 'None'}")
            
            # Use the new libsql.connect() function (DB-API style)
            self._conn = libsql.connect(
                database=self.url,
                auth_token=self.auth_token or ''
            )
            
            logger.info(f"✅ Connected successfully. Connection type: {type(self._conn).__name__}")
            
            # Initialize schema
            logger.info("Initializing database schema...")
            self._init_schema()
            logger.info("✅ Schema initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            logger.error(f"   URL: {self.url}")
            logger.error(f"   Connection type: {type(self._conn).__name__ if self._conn else 'None'}")
            raise
    
    def _init_schema(self):
        """Initialize database schema."""
        cursor = self._conn.cursor()
        
        try:
            # Create tasks table with sync metadata
            logger.debug("Creating tasks table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    due DATETIME,
                    priority TEXT,
                    status TEXT,
                    project TEXT,
                    tags TEXT,
                    notes TEXT,
                    dependencies TEXT,
                    recurrence_rule TEXT,
                    created_at DATETIME,
                    modified_at DATETIME,
                    completed_at DATETIME,
                    estimated_duration INTEGER,
                    actual_duration INTEGER,
                    is_recurring BOOLEAN,
                    recurring_task_id TEXT,
                    tasklist_id TEXT,
                    last_synced_at DATETIME,
                    source TEXT DEFAULT 'remote',
                    sync_version INTEGER DEFAULT 1
                )
            ''')
            logger.debug("   ✅ Tasks table created")
            
            # Create task_lists mapping table
            logger.debug("Creating task_lists table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_lists (
                    task_id TEXT PRIMARY KEY,
                    list_name TEXT NOT NULL
                )
            ''')
            logger.debug("   ✅ Task_lists table created")
            
            # Create indexes for better query performance
            logger.debug("Creating indexes...")
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_modified ON tasks(modified_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_source ON tasks(source)')
            logger.debug("   ✅ Indexes created")
            
            self._conn.commit()
            logger.debug("Remote database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
        finally:
            cursor.close()
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if self._conn is None:
                return False
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Save tasks to remote database using INSERT OR REPLACE to prevent duplicates.
        
        Args:
            tasks: List of task dictionaries to save
        """
        if not tasks:
            return
        
        try:
            logger.debug(f"Saving {len(tasks)} tasks to remote database")
            
            cursor = self._conn.cursor()
            for task in tasks:
                # Serialize list fields to JSON
                tags_json = json.dumps(task.get('tags', []))
                dependencies_json = json.dumps(task.get('dependencies', []))
                
                # Get or set sync metadata
                current_time = datetime.utcnow().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO tasks (
                        id, title, description, due, priority, status, project,
                        tags, notes, dependencies, recurrence_rule, created_at,
                        modified_at, completed_at, estimated_duration, actual_duration,
                        is_recurring, recurring_task_id, tasklist_id,
                        last_synced_at, source, sync_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    task.get('tasklist_id'),
                    current_time,
                    task.get('source', 'remote'),
                    task.get('sync_version', 1)
                ))
                
                # Save list mapping if available
                if task.get('list_name'):
                    cursor.execute('''
                        INSERT OR REPLACE INTO task_lists (task_id, list_name)
                        VALUES (?, ?)
                    ''', (task.get('id'), task.get('list_name')))
            
            self._conn.commit()
            cursor.close()
            logger.debug(f"Successfully saved {len(tasks)} tasks to remote database")
            
        except Exception as e:
            logger.error(f"Error saving tasks to remote database: {e}")
            raise
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """
        Load all tasks from remote database.
        
        Returns:
            List of task dictionaries
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute('''
                SELECT 
                    t.id, t.title, t.description, t.due, t.priority, t.status, t.project,
                    t.tags, t.notes, t.dependencies, t.recurrence_rule, t.created_at,
                    t.modified_at, t.completed_at, t.estimated_duration, t.actual_duration,
                    t.is_recurring, t.recurring_task_id, t.tasklist_id,
                    t.last_synced_at, t.source, t.sync_version,
                    l.list_name
                FROM tasks t
                LEFT JOIN task_lists l ON t.id = l.task_id
            ''')
            
            rows = cursor.fetchall()
            cursor.close()
            
            tasks = []
            for row in rows:
                task = self._row_to_task(row)
                tasks.append(task)
            
            logger.debug(f"Loaded {len(tasks)} tasks from remote database")
            return tasks
            
        except Exception as e:
            logger.error(f"Error loading tasks from remote database: {e}")
            return []
    
    def get_tasks_modified_since(self, since: datetime) -> List[Dict[str, Any]]:
        """
        Get tasks modified since given timestamp.
        
        Args:
            since: Datetime to check modifications from
            
        Returns:
            List of tasks modified since the given time
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                'SELECT * FROM tasks WHERE modified_at > ?',
                (since.isoformat(),)
            )
            
            rows = cursor.fetchall()
            cursor.close()
            
            tasks = []
            for row in rows:
                task = self._row_to_task(row)
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting modified tasks: {e}")
            return []
    
    def load_list_mapping(self) -> Dict[str, str]:
        """
        Load task list mappings from database.
        
        Returns:
            Dictionary mapping task IDs to list names
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute('SELECT task_id, list_name FROM task_lists')
            rows = cursor.fetchall()
            cursor.close()
            
            mappings = {row[0]: row[1] for row in rows}
            return mappings
            
        except Exception as e:
            logger.error(f"Error loading list mappings: {e}")
            return {}
    
    def save_list_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Save task list mappings to database.
        
        Args:
            mapping: Dictionary mapping task IDs to list names
        """
        try:
            cursor = self._conn.cursor()
            for task_id, list_name in mapping.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO task_lists (task_id, list_name)
                    VALUES (?, ?)
                ''', (task_id, list_name))
            
            self._conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error saving list mappings: {e}")
            raise
    
    def clear_tasks(self) -> None:
        """Clear all tasks from the remote database."""
        try:
            cursor = self._conn.cursor()
            cursor.execute('DELETE FROM tasks')
            cursor.execute('DELETE FROM task_lists')
            self._conn.commit()
            cursor.close()
            
            logger.debug("Cleared all tasks from remote database")
            
        except Exception as e:
            logger.error(f"Error clearing tasks: {e}")
            raise
    
    def get_task_count(self) -> int:
        """Get the total number of tasks in the database."""
        try:
            cursor = self._conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM tasks')
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting task count: {e}")
            return 0
    
    def close(self):
        """Close the database connection."""
        if self._conn:
            try:
                self._conn.close()
                logger.debug("Remote database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
    
    def _row_to_task(self, row) -> Dict[str, Any]:
        """
        Convert database row to task dictionary.
        
        Args:
            row: Database row tuple
            
        Returns:
            Task dictionary
        """
        return {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'due': row[3],
            'priority': row[4],
            'status': row[5],
            'project': row[6],
            'tags': json.loads(row[7]) if row[7] else [],
            'notes': row[8],
            'dependencies': json.loads(row[9]) if row[9] else [],
            'recurrence_rule': row[10],
            'created_at': row[11],
            'modified_at': row[12],
            'completed_at': row[13],
            'estimated_duration': row[14],
            'actual_duration': row[15],
            'is_recurring': row[16],
            'recurring_task_id': row[17],
            'tasklist_id': row[18],
            'last_synced_at': row[19],
            'source': row[20],
            'sync_version': row[21],
            'list_name': row[22] if len(row) > 22 else None
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
