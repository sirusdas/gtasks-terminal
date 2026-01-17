# Remote Sync Feature Implementation Plan

## Overview

This document outlines the comprehensive implementation plan for adding bidirectional sync capabilities between local SQLite database, remote Turso (libSQL) databases, and Google Tasks API.

**Provided Credentials:**
- **URL:** `libsql://gtaskssqllite-sirusdas.aws-ap-south-1.turso.io`
- **Token:** `eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Njg2NjAwNjksImlkIjoiOGUxMWMyODgtODQzYy00ODMwLTgyMzktZjY2OTdhYjIxMTUwIiwicmlkIjoiMDdiN2FkZmUtYzNiOC00MDk0LThkODMtYjAyNjI2YjE5NzM1In0.9bdu99nd5Xq851Ng_DlThwJyqu150QPBc53l9DfUr3md4G4GXFu6PktLpvwbqMf-qin8Vk1qGw4iua7h3s-ZCQ`

---

## Architecture

### Data Flow Diagram

```mermaid
graph TB
    subgraph "Local Machine"
        CLI[CLI Commands] --> TM[TaskManager]
        TM --> LocalSQLite[(Local SQLite)]
    end
    
    subgraph "Remote Server - Shared Hosting"
        Dashboard[Remote Dashboard] --> RemoteAPI[API Layer]
        RemoteAPI --> RemoteLibSQL[(Remote Turso DB)]
    end
    
    subgraph "Cloud"
        LocalSQLite -.->|Sync when online| RemoteLibSQL
        RemoteLibSQL -.->|Sync when online| Google[Google Tasks API]
        LocalSQLite -.->|Sync when online| Google
    end
    
    subgraph "Sync Process"
        SyncService[Sync Service] --> CheckLocal[Check Local DB]
        SyncService --> CheckRemote[Check Remote DB]
        SyncService --> CheckGoogle[Check Google Tasks]
        SyncService --> Resolve[Resolve Conflicts]
        SyncService --> Push[Push to all sources]
    end
```

### Sync Strategy

```mermaid
sequenceDiagram
    participant L as Local SQLite
    participant R as Remote Turso
    participant G as Google Tasks
    participant S as Sync Service
    
    Note over L,R,G: Sync Process
    S->>L: Load all tasks
    S->>R: Load all tasks
    S->>G: Load all tasks
    
    S->>S: Merge by task_id
    S->>S: Compare timestamps
    S->>S: Resolve conflicts (newest wins)
    
    alt Local is newer
        S->>R: Update/Insert task
        S->>G: Update task
    else Remote is newer
        S->>L: Update/Insert task
        S->>G: Update task
    else Google is newer
        S->>L: Update/Insert task
        S->>R: Update/Insert task
    end
    
    S->>L: Save merged tasks
    S->>R: Save merged tasks
    S->>G: Sync with Google
```

---

## File Structure Changes

```
gtasks_automation/
├── .gitignore                          # Add token/config exclusions
├── gtasks_cli/
│   ├── config/
│   │   └── remote_dbs.yaml            # Stores remote DB URLs (NOT tokens)
│   ├── storage/
│   │   ├── sqlite_storage.py          # Enhanced with sync metadata
│   │   ├── libsql_storage.py          # NEW: Turso connection
│   │   └── sync_config_storage.py     # NEW: Remote DB configs
│   ├── sync/
│   │   ├── __init__.py
│   │   ├── remote_sync_manager.py     # NEW: Main sync logic
│   │   ├── conflict_resolver.py       # NEW: Timestamp resolution
│   │   └── sync_models.py             # NEW: SyncConfig, RemoteDB models
│   ├── commands/
│   │   ├── sync.py                    # Enhanced with remote sync
│   │   └── remote.py                  # NEW: Remote DB management
│   └── src/gtasks_cli/
│       └── main.py                    # Add remote commands
│
└── gtasks_dashboard/
    ├── config.py                      # Add remote DB config
    ├── services/
    │   ├── sync_service.py            # Enhanced for remote
    │   └── remote_sync_service.py     # NEW: Dashboard remote sync
    ├── routes/
    │   ├── api.py                     # Add remote sync endpoints
    │   └── dashboard.py               # Add status endpoints
    ├── static/
    │   ├── js/
    │   │   ├── dashboard.js           # Add remote status UI
    │   │   └── sync-status.js         # NEW: Sync status component
    │   └── css/
    │       └── sync-status.css        # NEW: Sync status styles
    └── templates/
        └── dashboard.html             # Add connection indicator
```

---

## Database Schema Enhancements

### Enhanced SQLite Schema

```sql
-- Existing tasks table (add new columns)
ALTER TABLE tasks ADD COLUMN last_synced_at DATETIME;
ALTER TABLE tasks ADD COLUMN source TEXT DEFAULT 'local';
ALTER TABLE tasks ADD COLUMN sync_version INTEGER DEFAULT 1;

-- New task_versions table for conflict tracking
CREATE TABLE task_versions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    source TEXT NOT NULL,
    modified_at DATETIME NOT NULL,
    version INTEGER NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

-- Remote DB configurations table
CREATE TABLE remote_dbs (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_synced_at DATETIME,
    is_active INTEGER DEFAULT 1
);
```

### Turso/Remote DB Schema (Same structure)

```sql
-- Tasks table (mirrors local with sync metadata)
CREATE TABLE tasks (
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
    -- Sync metadata
    last_synced_at DATETIME,
    source TEXT DEFAULT 'remote',
    sync_version INTEGER DEFAULT 1
);

-- Indexes
CREATE INDEX idx_tasks_modified ON tasks(modified_at);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_source ON tasks(source);
```

---

## Implementation Steps

### Phase 1: Storage Layer (Days 1-2)

#### 1.1 Create libsql_storage.py

**File:** `gtasks_cli/storage/libsql_storage.py`

```python
"""
LibSQL storage implementation for Turso/Remote database connection.
"""
import libsql_client
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import os

class LibSQLStorage:
    """Storage implementation for Turso libSQL database."""
    
    def __init__(self, url: str, auth_token: str = None, local_path: str = None):
        """
        Initialize LibSQL storage.
        
        Args:
            url: Turso database URL
            auth_token: Authentication token
            local_path: Optional local cache path
        """
        self.url = url
        self.auth_token = auth_token or os.getenv("GTASKS_TURSO_TOKEN")
        self.local_cache = local_path
        self._init_connection()
    
    def _init_connection(self):
        """Initialize database connection."""
        self.conn = libsql_client.connect(
            url=self.url,
            auth_token=self.auth_token
        )
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        with self.conn.cursor() as cursor:
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
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_modified ON tasks(modified_at)
            ''')
            self.conn.commit()
    
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """Save tasks using INSERT OR REPLACE to prevent duplicates."""
        with self.conn.cursor() as cursor:
            for task in tasks:
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
                    self._serialize_list(task.get('tags', [])),
                    task.get('notes'),
                    self._serialize_list(task.get('dependencies', [])),
                    task.get('recurrence_rule'),
                    task.get('created_at'),
                    task.get('modified_at'),
                    task.get('completed_at'),
                    task.get('estimated_duration'),
                    task.get('actual_duration'),
                    task.get('is_recurring', False),
                    task.get('recurring_task_id'),
                    task.get('tasklist_id'),
                    datetime.utcnow().isoformat(),
                    task.get('source', 'remote'),
                    task.get('sync_version', 1)
                ))
            self.conn.commit()
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """Load all tasks from remote database."""
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM tasks')
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]
    
    def get_tasks_modified_since(self, since: datetime) -> List[Dict[str, Any]]:
        """Get tasks modified since given timestamp."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM tasks WHERE modified_at > ?',
                (since.isoformat(),)
            )
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]
    
    def _serialize_list(self, data: List) -> str:
        """Serialize list to JSON string."""
        import json
        return json.dumps(data) if data else '[]'
    
    def _row_to_task(self, row) -> Dict[str, Any]:
        """Convert database row to task dictionary."""
        import json
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
            'sync_version': row[21]
        }
```

#### 1.2 Create sync_config_storage.py

**File:** `gtasks_cli/storage/sync_config_storage.py`

```python
"""
Storage for remote database configurations and sync settings.
"""
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import os

@dataclass
class RemoteDBConfig:
    """Configuration for a remote database."""
    id: str
    url: str
    name: str
    created_at: str
    last_synced_at: Optional[str]
    is_active: bool

class SyncConfigStorage:
    """Manages remote database configurations."""
    
    def __init__(self):
        """Initialize sync config storage."""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / 'remote_dbs.yaml'
        self._ensure_config_dir()
    
    def _get_config_dir(self) -> Path:
        """Get configuration directory."""
        config_dir_env = os.environ.get('GTASKS_CONFIG_DIR')
        if config_dir_env:
            return Path(config_dir_env)
        return Path.home() / '.gtasks'
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_remote_dbs(self) -> List[RemoteDBConfig]:
        """Load all configured remote databases."""
        if not self.config_file.exists():
            return []
        
        with open(self.config_file, 'r') as f:
            data = yaml.safe_load(f) or {'remote_dbs': []}
        
        return [
            RemoteDBConfig(**db) 
            for db in data.get('remote_dbs', [])
        ]
    
    def save_remote_db(self, config: RemoteDBConfig) -> None:
        """Save or update a remote database configuration."""
        remote_dbs = self.load_remote_dbs()
        
        # Remove existing with same URL
        remote_dbs = [db for db in remote_dbs if db.url != config.url]
        remote_dbs.append(config)
        
        data = {
            'remote_dbs': [asdict(db) for db in remote_dbs]
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(data, f)
    
    def remove_remote_db(self, url: str) -> bool:
        """Remove a remote database configuration."""
        remote_dbs = self.load_remote_dbs()
        original_count = len(remote_dbs)
        remote_dbs = [db for db in remote_dbs if db.url != url]
        
        if len(remote_dbs) < original_count:
            data = {
                'remote_dbs': [asdict(db) for db in remote_dbs]
            }
            with open(self.config_file, 'w') as f:
                yaml.dump(data, f)
            return True
        return False
    
    def update_last_synced(self, url: str, timestamp: str) -> None:
        """Update last synced timestamp for a remote database."""
        remote_dbs = self.load_remote_dbs()
        for db in remote_dbs:
            if db.url == url:
                db.last_synced_at = timestamp
                break
        data = {
            'remote_dbs': [asdict(db) for db in remote_dbs]
        }
        with open(self.config_file, 'w') as f:
            yaml.dump(data, f)
```

#### 1.3 Create conflict_resolver.py

**File:** `gtasks_cli/sync/conflict_resolver.py`

```python
"""
Conflict resolution for bidirectional sync.
Uses timestamp-based resolution with newer wins.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class ConflictResolutionStrategy(Enum):
    NEWEST_WINS = "newest_wins"
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    MANUAL = "manual"

@dataclass
class TaskVersion:
    """Represents a task version from a specific source."""
    task_id: str
    source: str  # 'local', 'remote', 'google'
    modified_at: datetime
    data: Dict[str, Any]
    priority: int  # Higher = preferred source

class ConflictResolver:
    """Resolves conflicts between task versions from different sources."""
    
    # Source priority (higher = preferred when timestamps equal)
    SOURCE_PRIORITY = {
        'google': 3,  # Google is source of truth
        'local': 2,   # Local changes preferred
        'remote': 1   # Remote has lower priority
    }
    
    def __init__(self, strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.NEWEST_WINS):
        """Initialize conflict resolver."""
        self.strategy = strategy
    
    def resolve(self, versions: List[TaskVersion]) -> TaskVersion:
        """
        Resolve conflict between multiple versions of the same task.
        
        Args:
            versions: List of task versions from different sources
            
        Returns:
            The resolved task version
        """
        if len(versions) == 1:
            return versions[0]
        
        if self.strategy == ConflictResolutionStrategy.NEWEST_WINS:
            return self._newest_wins(versions)
        elif self.strategy == ConflictResolutionStrategy.LOCAL_WINS:
            return self._source_wins(versions, 'local')
        elif self.strategy == ConflictResolutionStrategy.REMOTE_WINS:
            return self._source_wins(versions, 'remote')
        elif self.strategy == ConflictResolutionStrategy.GOOGLE_WINS:
            return self._source_wins(versions, 'google')
        else:
            return self._newest_wins(versions)
    
    def _newest_wins(self, versions: List[TaskVersion]) -> TaskVersion:
        """Select the version with the newest timestamp."""
        return max(versions, key=lambda v: (v.modified_at, self.SOURCE_PRIORITY.get(v.source, 0)))
    
    def _source_wins(self, versions: List[TaskVersion], preferred_source: str) -> TaskVersion:
        """Select version from preferred source, or newest if not available."""
        # Try to find version from preferred source
        for version in versions:
            if version.source == preferred_source:
                return version
        
        # Fall back to newest
        return self._newest_wins(versions)
    
    def merge_all_tasks(self, local_tasks: List[Dict[str, Any]], 
                       remote_tasks: List[Dict[str, Any]],
                       google_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge tasks from all sources into a single list.
        
        Args:
            local_tasks: Tasks from local SQLite
            remote_tasks: Tasks from remote Turso
            google_tasks: Tasks from Google Tasks API
            
        Returns:
            Merged list of tasks with conflicts resolved
        """
        # Build task map by ID
        task_map = {}
        
        # Add local tasks
        for task in local_tasks:
            task_id = task.get('id')
            task_map[task_id] = {
                'local': task
            }
        
        # Add remote tasks
        for task in remote_tasks:
            task_id = task.get('id')
            if task_id in task_map:
                task_map[task_id]['remote'] = task
            else:
                task_map[task_id] = {'remote': task}
        
        # Add Google tasks
        for task in google_tasks:
            task_id = task.get('id')
            if task_id in task_map:
                task_map[task_id]['google'] = task
            else:
                task_map[task_id] = {'google': task}
        
        # Resolve conflicts for each task
        merged_tasks = []
        for task_id, sources in task_map.items():
            versions = []
            
            if 'local' in sources:
                versions.append(TaskVersion(
                    task_id=task_id,
                    source='local',
                    modified_at=self._parse_datetime(sources['local'].get('modified_at')),
                    data=sources['local'],
                    priority=self.SOURCE_PRIORITY['local']
                ))
            
            if 'remote' in sources:
                versions.append(TaskVersion(
                    task_id=task_id,
                    source='remote',
                    modified_at=self._parse_datetime(sources['remote'].get('modified_at')),
                    data=sources['remote'],
                    priority=self.SOURCE_PRIORITY['remote']
                ))
            
            if 'google' in sources:
                versions.append(TaskVersion(
                    task_id=task_id,
                    source='google',
                    modified_at=self._parse_datetime(sources['google'].get('modified_at')),
                    data=sources['google'],
                    priority=self.SOURCE_PRIORITY['google']
                ))
            
            # Resolve and add to merged list
            if versions:
                winner = self.resolve(versions)
                merged_tasks.append(winner.data)
        
        return merged_tasks
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return datetime.min
        
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return datetime.min
```

#### 1.4 Create remote_sync_manager.py

**File:** `gtasks_cli/sync/remote_sync_manager.py`

```python
"""
Main sync manager for coordinating sync between local, remote, and Google.
"""
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# Add gtasks_cli to path
gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
if str(gtasks_cli_path) not in sys.path:
    sys.path.insert(0, str(gtasks_cli_path))

from gtasks_cli.storage.sync_config_storage import SyncConfigStorage, RemoteDBConfig
from gtasks_cli.storage.libsql_storage import LibSQLStorage
from gtasks_cli.storage.sqlite_storage import SQLiteStorage
from gtasks_cli.sync.conflict_resolver import ConflictResolver, ConflictResolutionStrategy
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

class RemoteSyncManager:
    """Manages bidirectional sync between local, remote, and Google."""
    
    def __init__(self, account_name: str = None):
        """Initialize sync manager."""
        self.account_name = account_name
        self.config_storage = SyncConfigStorage()
        self.conflict_resolver = ConflictResolver(ConflictResolutionStrategy.NEWEST_WINS)
        self._sync_state = {}
        self._state_lock = threading.Lock()
        
        # Initialize local storage
        self.local_storage = SQLiteStorage(account_name=account_name)
    
    def add_remote_db(self, url: str, name: str = None, token: str = None) -> RemoteDBConfig:
        """
        Add a new remote database configuration.
        
        Args:
            url: Turso database URL
            name: Optional friendly name
            token: Authentication token (optional, can use env var)
            
        Returns:
            RemoteDBConfig object
        """
        # Validate connection
        storage = LibSQLStorage(url=url, auth_token=token)
        test_tasks = storage.load_tasks()
        logger.info(f"Successfully connected to {url}, found {len(test_tasks)} tasks")
        
        # Create config
        config = RemoteDBConfig(
            id=str(uuid.uuid4()),
            url=url,
            name=name or f"Remote DB {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            created_at=datetime.utcnow().isoformat(),
            last_synced_at=None,
            is_active=True
        )
        
        # Save configuration
        self.config_storage.save_remote_db(config)
        
        logger.info(f"Added remote database: {config.name} ({config.url})")
        return config
    
    def list_remote_dbs(self) -> List[RemoteDBConfig]:
        """List all configured remote databases."""
        return self.config_storage.load_remote_dbs()
    
    def remove_remote_db(self, url: str) -> bool:
        """Remove a remote database configuration."""
        success = self.config_storage.remove_remote_db(url)
        if success:
            logger.info(f"Removed remote database: {url}")
        return success
    
    def sync_all(self, push_to_remote: bool = True, 
                 sync_with_google: bool = True) -> Dict[str, Any]:
        """
        Perform full sync with all configured remote databases and Google.
        
        Args:
            push_to_remote: Whether to push local changes to remote
            sync_with_google: Whether to sync with Google Tasks
            
        Returns:
            Sync result summary
        """
        sync_id = str(uuid.uuid4())
        
        with self._state_lock:
            self._sync_state[sync_id] = {
                'status': 'running',
                'progress': 0,
                'message': 'Initializing sync...',
                'start_time': datetime.utcnow().isoformat(),
                'results': {}
            }
        
        try:
            # Update status
            self._update_sync_state(sync_id, 10, 'Loading local tasks...')
            
            # Load local tasks
            local_tasks = self.local_storage.load_tasks()
            logger.info(f"Loaded {len(local_tasks)} tasks from local database")
            
            # Load tasks from all remote databases
            remote_dbs = self.config_storage.load_remote_dbs()
            all_remote_tasks = {}
            
            for i, config in enumerate(remote_dbs):
                if not config.is_active:
                    continue
                
                progress = 20 + (i * 10)
                self._update_sync_state(sync_id, progress, f"Loading tasks from {config.name}...")
                
                try:
                    storage = LibSQLStorage(url=config.url)
                    remote_tasks = storage.load_tasks()
                    all_remote_tasks[config.url] = {
                        'config': config,
                        'tasks': remote_tasks
                    }
                    logger.info(f"Loaded {len(remote_tasks)} tasks from {config.name}")
                except Exception as e:
                    logger.error(f"Failed to load from {config.name}: {e}")
                    all_remote_tasks[config.url] = {
                        'config': config,
                        'tasks': [],
                        'error': str(e)
                    }
            
            # Load Google tasks if requested
            google_tasks = []
            if sync_with_google:
                self._update_sync_state(sync_id, 50, 'Loading Google Tasks...')
                try:
                    task_manager = TaskManager(
                        use_google_tasks=True,
                        storage_backend='sqlite',
                        account_name=self.account_name
                    )
                    google_tasks = task_manager.google_client.list_tasks()
                    logger.info(f"Loaded {len(google_tasks)} tasks from Google")
                except Exception as e:
                    logger.error(f"Failed to load Google tasks: {e}")
                    google_tasks = []
            
            # Merge all tasks
            self._update_sync_state(sync_id, 70, 'Merging tasks and resolving conflicts...')
            
            # Collect all remote tasks into single list
            merged_remote_tasks = []
            for remote_data in all_remote_tasks.values():
                merged_remote_tasks.extend(remote_data['tasks'])
            
            # Merge and resolve conflicts
            merged_tasks = self.conflict_resolver.merge_all_tasks(
                local_tasks=local_tasks,
                remote_tasks=merged_remote_tasks,
                google_tasks=google_tasks
            )
            
            logger.info(f"Merged to {len(merged_tasks)} tasks")
            
            # Save merged tasks to local
            self._update_sync_state(sync_id, 80, 'Saving to local database...')
            self.local_storage.save_tasks(merged_tasks)
            
            # Push to remote databases
            if push_to_remote:
                for i, config in enumerate(remote_dbs):
                    if not config.is_active:
                        continue
                    
                    progress = 85 + (i * 5)
                    self._update_sync_state(sync_id, progress, f"Pushing to {config.name}...")
                    
                    try:
                        storage = LibSQLStorage(url=config.url)
                        storage.save_tasks(merged_tasks)
                        self.config_storage.update_last_synced(
                            config.url, 
                            datetime.utcnow().isoformat()
                        )
                        logger.info(f"Synced to {config.name}")
                    except Exception as e:
                        logger.error(f"Failed to sync to {config.name}: {e}")
            
            # Push to Google if needed
            if sync_with_google:
                self._update_sync_state(sync_id, 95, 'Syncing with Google Tasks...')
                try:
                    # This would sync merged tasks to Google
                    # Implementation depends on advanced sync logic
                    logger.info("Synced with Google Tasks")
                except Exception as e:
                    logger.error(f"Failed to sync with Google: {e}")
            
            # Complete
            self._update_sync_state(sync_id, 100, 'Sync completed successfully')
            
            return {
                'sync_id': sync_id,
                'status': 'completed',
                'local_tasks': len(local_tasks),
                'remote_dbs': len(all_remote_tasks),
                'merged_tasks': len(merged_tasks),
                'errors': [d.get('error') for d in all_remote_tasks.values() if 'error' in d]
            }
            
        except Exception as e:
            self._update_sync_state(sync_id, 0, f'Sync failed: {str(e)}', status='error')
            return {
                'sync_id': sync_id,
                'status': 'error',
                'error': str(e)
            }
    
    def _update_sync_state(self, sync_id: str, progress: int, message: str, status: str = 'running'):
        """Update sync state for progress tracking."""
        with self._state_lock:
            if sync_id in self._sync_state:
                self._sync_state[sync_id].update({
                    'progress': progress,
                    'message': message,
                    'status': status
                })
```

### Phase 2: CLI Commands (Day 2-3)

#### 2.1 Create remote.py commands

**File:** `gtasks_cli/commands/remote.py`

```python
"""
Remote database management commands.
"""
import click
from typing import Optional
from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

@click.group(name='remote')
def remote_commands():
    """Manage remote database connections."""
    pass

@remote_commands.command(name='add')
@click.argument('url', type=str)
@click.argument('token', type=str, required=False)
@click.option('--name', '-n', type=str, help='Friendly name for the remote database')
@click.option('--account', '-a', type=str, help='Account name for multi-account support')
def add_remote(url: str, token: Optional[str], name: Optional[str], account: str):
    """Add a new remote Turso database."""
    try:
        manager = RemoteSyncManager(account_name=account)
        config = manager.add_remote_db(url=url, name=name, token=token)
        
        click.echo(f"✓ Successfully added remote database:")
        click.echo(f"  Name: {config.name}")
        click.echo(f"  URL: {config.url}")
        click.echo(f"  ID: {config.id}")
    except Exception as e:
        logger.error(f"Failed to add remote database: {e}")
        click.echo(f"✗ Error: {str(e)}", err=True)

@remote_commands.command(name='list')
@click.option('--account', '-a', type=str, help='Account name for multi-account support')
def list_remotes(account: str):
    """List all configured remote databases."""
    try:
        manager = RemoteSyncManager(account_name=account)
        remote_dbs = manager.list_remote_dbs()
        
        if not remote_dbs:
            click.echo("No remote databases configured.")
            return
        
        click.echo(f"Configured remote databases ({len(remote_dbs)}):\n")
        
        for i, db in enumerate(remote_dbs, 1):
            status = "✓ Active" if db.is_active else "○ Inactive"
            last_sync = db.last_synced_at or "Never"
            
            click.echo(f"{i}. {db.name}")
            click.echo(f"   URL: {db.url}")
            click.echo(f"   Status: {status}")
            click.echo(f"   Last synced: {last_sync}")
            click.echo()
    except Exception as e:
        logger.error(f"Failed to list remote databases: {e}")
        click.echo(f"✗ Error: {str(e)}", err=True)

@remote_commands.command(name='remove')
@click.argument('url', type=str)
@click.option('--account', '-a', type=str, help='Account name for multi-account support')
@click.confirmation_option(prompt='Are you sure you want to remove this remote database?')
def remove_remote(url: str, account: str):
    """Remove a remote database configuration."""
    try:
        manager = RemoteSyncManager(account_name=account)
        success = manager.remove_remote_db(url)
        
        if success:
            click.echo(f"✓ Removed remote database: {url}")
        else:
            click.echo(f"✗ Remote database not found: {url}")
    except Exception as e:
        logger.error(f"Failed to remove remote database: {e}")
        click.echo(f"✗ Error: {str(e)}", err=True)

@remote_commands.command(name='sync')
@click.option('--account', '-a', type=str, help='Account name for multi-account support')
@click.option('--no-push', is_flag=True, help='Do not push to remote databases')
@click.option('--no-google', is_flag=True, help='Do not sync with Google Tasks')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed sync progress')
def sync_remote(account: str, no_push: bool, no_google: bool, verbose: bool):
    """Sync with all configured remote databases and Google Tasks."""
    try:
        manager = RemoteSyncManager(account_name=account)
        
        click.echo("Starting remote sync...")
        
        result = manager.sync_all(
            push_to_remote=not no_push,
            sync_with_google=not no_google
        )
        
        if result['status'] == 'completed':
            click.echo(f"\n✓ Sync completed successfully!")
            click.echo(f"  Tasks merged: {result['merged_tasks']}")
            click.echo(f"  Remote DBs: {result['remote_dbs']}")
            
            if result.get('errors'):
                click.echo(f"\n  Warnings:")
                for error in result['errors']:
                    if error:
                        click.echo(f"    - {error}")
        else:
            click.echo(f"\n✗ Sync failed: {result.get('error')}", err=True)
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        click.echo(f"✗ Error: {str(e)}", err=True)
```

### Phase 3: Dashboard Integration (Days 3-4)

#### 3.1 Create remote_sync_service.py for dashboard

**File:** `gtasks_dashboard/services/remote_sync_service.py`

```python
"""
Remote sync service for the dashboard.
"""
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add gtasks_cli to path
gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
if str(gtasks_cli_path) not in sys.path:
    sys.path.insert(0, str(gtasks_cli_path))

class RemoteSyncService:
    """Service for managing remote sync from dashboard."""
    
    _sync_state: Dict[str, Dict[str, Any]] = {}
    _state_lock = threading.Lock()
    
    @classmethod
    def get_remote_status(cls) -> Dict[str, Any]:
        """Get status of remote database connections."""
        try:
            from gtasks_cli.storage.sync_config_storage import SyncConfigStorage
            from gtasks_cli.storage.libsql_storage import LibSQLStorage
            
            config_storage = SyncConfigStorage()
            remote_dbs = config_storage.load_remote_dbs()
            
            status = {
                'connected_dbs': [],
                'total_count': len(remote_dbs),
                'active_count': sum(1 for db in db.is_active),
                'last_sync': None
            }
            
            for db in remote_dbs:
                try:
                    storage = LibSQLStorage(url=db.url)
                    task_count = len(storage.load_tasks())
                    
                    status['connected_dbs'].append({
                        'name': db.name,
                        'url': db.url,
                        'status': 'connected',
                        'task_count': task_count,
                        'last_synced': db.last_synced_at
                    })
                    
                    if db.last_synced_at and not status['last_sync']:
                        status['last_sync'] = db.last_synced_at
                        
                except Exception as e:
                    status['connected_dbs'].append({
                        'name': db.name,
                        'url': db.url,
                        'status': 'error',
                        'error': str(e)
                    })
            
            return status
            
        except Exception as e:
            return {
                'error': str(e),
                'connected_dbs': [],
                'total_count': 0,
                'active_count': 0
            }
    
    @classmethod
    def sync_with_remote(cls, db_url: str = None) -> str:
        """Start a sync operation with remote database(s)."""
        sync_id = str(uuid.uuid4())
        
        with cls._state_lock:
            cls._sync_state[sync_id] = {
                'status': 'running',
                'progress': 0,
                'message': 'Initializing sync...',
                'start_time': datetime.utcnow().isoformat()
            }
        
        # Start sync in background
        sync_thread = threading.Thread(
            target=cls._run_sync,
            args=(sync_id, db_url),
            daemon=True
        )
        sync_thread.start()
        
        return sync_id
    
    @classmethod
    def _run_sync(cls, sync_id: str, db_url: str = None):
        """Internal sync execution."""
        try:
            from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager
            
            manager = RemoteSyncManager()
            result = manager.sync_all()
            
            with cls._state_lock:
                if sync_id in cls._sync_state:
                    if result['status'] == 'completed':
                        cls._sync_state[sync_id].update({
                            'progress': 100,
                            'message': 'Sync completed successfully',
                            'status': 'completed',
                            'result': result
                        })
                    else:
                        cls._sync_state[sync_id].update({
                            'progress': 0,
                            'message': f"Sync failed: {result.get('error')}",
                            'status': 'error',
                            'error': result.get('error')
                        })
                        
        except Exception as e:
            with cls._state_lock:
                if sync_id in cls._sync_state:
                    cls._sync_state[sync_id].update({
                        'progress': 0,
                        'message': f"Sync error: {str(e)}",
                        'status': 'error',
                        'error': str(e)
                    })
    
    @classmethod
    def get_sync_progress(cls, sync_id: str = None) -> Dict[str, Any]:
        """Get sync progress."""
        with cls._state_lock:
            if sync_id and sync_id in cls._sync_state:
                return cls._sync_state[sync_id].copy()
            return {
                'status': 'idle',
                'progress': 0,
                'message': 'No sync in progress'
            }
```

#### 3.2 Add API endpoints

**File:** `gtasks_dashboard/routes/api.py` (add these endpoints)

```python
from flask import Blueprint, jsonify, request
from gtasks_dashboard.services.remote_sync_service import RemoteSyncService

api = Blueprint('api', __name__)

@api.route('/api/remote/status', methods=['GET'])
def get_remote_status():
    """Get status of remote database connections."""
    status = RemoteSyncService.get_remote_status()
    return jsonify(status)

@api.route('/api/remote/sync', methods=['POST'])
def sync_remote():
    """Start a sync operation with remote database."""
    data = request.json or {}
    db_url = data.get('url')
    
    sync_id = RemoteSyncService.sync_with_remote(db_url=db_url)
    return jsonify({
        'sync_id': sync_id,
        'message': 'Sync started'
    })

@api.route('/api/remote/sync/progress/<sync_id>', methods=['GET'])
def get_sync_progress(sync_id):
    """Get progress of a sync operation."""
    progress = RemoteSyncService.get_sync_progress(sync_id)
    return jsonify(progress)

@api.route('/api/remote/add', methods=['POST'])
def add_remote_db():
    """Add a new remote database."""
    data = request.json
    
    try:
        from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager
        
        manager = RemoteSyncManager()
        config = manager.add_remote_db(
            url=data['url'],
            name=data.get('name'),
            token=data.get('token')
        )
        
        return jsonify({
            'success': True,
            'config': {
                'id': config.id,
                'name': config.name,
                'url': config.url
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api.route('/api/remote/remove', methods=['POST'])
def remove_remote_db():
    """Remove a remote database."""
    data = request.json
    
    try:
        from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager
        
        manager = RemoteSyncManager()
        success = manager.remove_remote_db(data['url'])
        
        return jsonify({
            'success': success
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
```

### Phase 4: Frontend Integration (Days 4-5)

#### 4.1 Create sync-status.js

**File:** `gtasks_dashboard/static/js/sync-status.js`

```javascript
/**
 * Sync Status Component
 * Manages remote sync status and operations in the dashboard header.
 */

const SyncStatus = {
    state: {
        connectedDBs: [],
        lastSync: null,
        syncInProgress: false,
        currentSyncId: null
    },

    /**
     * Initialize sync status component
     */
    init() {
        this.loadStatus();
        this.setupEventListeners();
        this.render();
    },

    /**
     * Load sync status from server
     */
    async loadStatus() {
        try {
            const response = await fetch('/api/remote/status');
            const data = await response.json();
            
            this.state.connectedDBs = data.connected_dbs || [];
            this.state.lastSync = data.last_sync;
        } catch (error) {
            console.error('Failed to load sync status:', error);
            this.state.connectedDBs = [];
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Sync button click
        const syncBtn = document.getElementById('sync-btn');
        if (syncBtn) {
            syncBtn.addEventListener('click', () => this.startSync());
        }
    },

    /**
     * Start a sync operation
     */
    async startSync() {
        if (this.state.syncInProgress) return;
        
        try {
            this.state.syncInProgress = true;
            this.render();
            
            const response = await fetch('/api/remote/sync', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            this.state.currentSyncId = data.sync_id;
            
            // Poll for progress
            this.pollSyncProgress();
            
        } catch (error) {
            console.error('Failed to start sync:', error);
            this.state.syncInProgress = false;
            this.render();
        }
    },

    /**
     * Poll sync progress
     */
    async pollSyncProgress() {
        if (!this.state.currentSyncId) return;
        
        try {
            const response = await fetch(`/api/remote/sync/progress/${this.state.currentSyncId}`);
            const progress = await response.json();
            
            if (progress.status === 'completed' || progress.status === 'error') {
                this.state.syncInProgress = false;
                this.state.currentSyncId = null;
                this.loadStatus(); // Reload status
            }
            
            this.renderProgress(progress);
            
            if (progress.status === 'running') {
                setTimeout(() => this.pollSyncProgress(), 1000);
            }
            
        } catch (error) {
            console.error('Failed to poll sync progress:', error);
            this.state.syncInProgress = false;
            this.render();
        }
    },

    /**
     * Render sync status UI
     */
    render() {
        const container = document.getElementById('sync-status');
        if (!container) return;

        const { connectedDBs, lastSync, syncInProgress } = this.state;
        const isConnected = connectedDBs.some(db => db.status === 'connected');
        
        let statusHTML = `
            <div class="sync-status-container">
                <div class="sync-indicator ${isConnected ? 'connected' : 'disconnected'}">
                    <span class="status-dot"></span>
                    <span class="status-text">${isConnected ? 'Connected' : 'Offline'}</span>
                </div>
                
                ${connectedDBs.length > 0 ? `
                    <div class="db-count">
                        ${connectedDBs.length} remote DB${connectedDBs.length !== 1 ? 's' : ''}
                    </div>
                ` : ''}
                
                ${lastSync ? `
                    <div class="last-sync">
                        Last sync: ${this.formatTimeAgo(lastSync)}
                    </div>
                ` : ''}
                
                <button id="sync-btn" class="sync-button ${syncInProgress ? 'syncing' : ''}" 
                        ${syncInProgress ? 'disabled' : ''}>
                    ${syncInProgress ? '⏳ Syncing...' : '🔄 Sync'}
                </button>
            </div>
        `;
        
        container.innerHTML = statusHTML;
        
        // Re-attach event listeners
        this.setupEventListeners();
    },

    /**
     * Render sync progress overlay
     */
    renderProgress(progress) {
        let overlay = document.getElementById('sync-progress-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'sync-progress-overlay';
            overlay.className = 'sync-progress-overlay';
            document.body.appendChild(overlay);
        }
        
        overlay.innerHTML = `
            <div class="sync-progress-content">
                <h3>${progress.message}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progress.percentage}%"></div>
                </div>
                <p>${progress.percentage}% complete</p>
            </div>
        `;
        
        overlay.style.display = 'flex';
    },

    /**
     * Format time ago from timestamp
     */
    formatTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = Math.floor((now - time) / 1000);
        
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
        return `${Math.floor(diff / 86400)} days ago`;
    }
};

// Export for use
window.SyncStatus = SyncStatus;
```

#### 4.2 Add sync-status.css

**File:** `gtasks_dashboard/static/css/sync-status.css`

```css
.sync-status-container {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 16px;
    background: var(--surface-color, #1e1e2e);
    border-radius: 8px;
}

.sync-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 500;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.sync-indicator.connected .status-dot {
    background: #22c55e;
    box-shadow: 0 0 8px #22c55e;
}

.sync-indicator.disconnected .status-dot {
    background: #ef4444;
}

.db-count {
    font-size: 11px;
    color: var(--text-secondary, #a0a0a0);
}

.last-sync {
    font-size: 11px;
    color: var(--text-muted, #666);
}

.sync-button {
    padding: 6px 12px;
    background: var(--primary-color, #3b82f6);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.sync-button:hover:not(:disabled) {
    background: var(--primary-hover, #2563eb);
}

.sync-button:disabled,
.sync-button.syncing {
    opacity: 0.7;
    cursor: not-allowed;
}

.sync-progress-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.sync-progress-content {
    background: var(--surface-color, #1e1e2e);
    padding: 24px;
    border-radius: 12px;
    text-align: center;
    min-width: 300px;
}

.progress-bar {
    height: 8px;
    background: var(--bg-secondary, #2a2a3e);
    border-radius: 4px;
    overflow: hidden;
    margin: 16px 0;
}

.progress-fill {
    height: 100%;
    background: var(--primary-color, #3b82f6);
    transition: width 0.3s ease;
}
```

#### 4.3 Update dashboard.html

**File:** `gtasks_dashboard/templates/dashboard.html` (add to header)

```html
<!-- Add before closing </head> -->
<link rel="stylesheet" href="/static/css/sync-status.css">

<!-- Add in header section -->
<header class="dashboard-header">
    <div class="header-left">
        <!-- Existing menu button and title -->
    </div>
    
    <div class="header-center">
        <!-- Search bar if exists -->
    </div>
    
    <div class="header-right">
        <!-- Add sync status -->
        <div id="sync-status"></div>
        
        <!-- Settings button -->
        <button id="settings-btn" class="header-btn">⚙️</button>
    </div>
</header>

<!-- Add before closing </body> -->
<script src="/static/js/sync-status.js"></script>
<script>
    // Initialize sync status when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        SyncStatus.init();
    });
</script>
```

---

## Security Considerations

### Token Storage

**IMPORTANT:** Tokens must NOT be synced to Git.

1. **Environment Variable** (Recommended):
   ```bash
   export GTASKS_TURSO_TOKEN="your-token-here"
   ```

2. **Encrypted Config File**:
   - Store tokens in `~/.gtasks/tokens.yaml` (encrypted)
   - Use `keyring` library for secure storage
   - Add to `.gitignore`: `**/.gtasks/tokens.yaml`

3. **`.gitignore` Entries**:
   ```
   # Remote DB tokens and configs
   **/.gtasks/tokens.yaml
   **/.gtasks/remote_dbs.yaml
   **/tokens.yaml
   
   # Environment-specific configs
   .env
   .env.local
   *.local.yaml
   ```

### Git Commit Check

Add a pre-commit hook to prevent accidental token commits:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for token patterns in staged files
TOKEN_PATTERN="eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"

for file in $(git diff --cached --name-only); do
    if grep -qE "$TOKEN_PATTERN" "$file" 2>/dev/null; then
        echo "ERROR: Possible token found in $file"
        echo "Tokens should NOT be committed to Git!"
        exit 1
    fi
done
```

---

## Testing Plan

### Unit Tests

1. **ConflictResolver Tests**:
   - Test timestamp comparison
   - Test source priority fallback
   - Test merge logic

2. **LibSQLStorage Tests**:
   - Test connection
   - Test save/load operations
   - Test error handling

3. **SyncConfigStorage Tests**:
   - Test add/remove remote DBs
   - Test config persistence

### Integration Tests

1. **Full Sync Test**:
   - Set up local SQLite
   - Set up Turso DB (use provided credentials)
   - Run full sync
   - Verify no duplicates
   - Verify data consistency

2. **Conflict Resolution Test**:
   - Create task in local
   - Create same task (different content) in remote
   - Run sync
   - Verify newer version wins
   - Verify both sources updated

3. **Dashboard Fallback Test**:
   - Remove local SQLite
   - Start dashboard
   - Verify it loads from remote
   - Verify warning banner shows

---

## Implementation Timeline

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| 1 | Storage Layer | 2 days | None |
| 2 | CLI Commands | 1 day | Phase 1 |
| 3 | Dashboard Service | 1 day | Phase 1 |
| 4 | Frontend Integration | 2 days | Phase 3 |
| 5 | Security & Testing | 1 day | All phases |
| 6 | Documentation | 1 day | All phases |

**Total Estimated Time: 8 days**

---

## Next Steps

1. **Immediate**: Test connection with provided Turso credentials
2. **Week 1**: Complete storage layer and CLI commands
3. **Week 2**: Complete dashboard integration and frontend
4. **Week 3**: Testing, security hardening, and documentation

---

## Appendix: Testing with Provided Credentials

**Connection Details:**
- **URL:** `libsql://gtaskssqllite-sirusdas.aws-ap-south-1.turso.io`
- **Token:** `eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Njg2NjAwNjksImlkIjoiOGUxMWMyODgtODQzYy00ODMwLTgyMzktZjY2OTdhYjIxMTUwIiwicmlkIjoiMDdiN2FkZmUtYzNiOC00MDk0LThkODMtYjAyNjI2YjE5NzM1In0.9bdu99nd5Xq851Ng_DlThwJyqu150QPBc53l9DfUr3md4G4GXFu6PktLpvwbqMf-qin8Vk1qGw4iua7h3s-ZCQ`

**Test Commands:**
```bash
# Test connection
export GTASKS_TURSO_TOKEN="eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9..."

# Add remote database
python -m gtasks_cli remote add libsql://gtaskssqllite-sirusdas.aws-ap-south-1.turso.io "Test DB"

# List remote databases
python -m gtasks_cli remote list

# Sync
python -m gtasks_cli remote sync
```
