"""
Remote sync service for the dashboard.
Provides API endpoints and sync operations for remote database management.
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
    
    # Thread-safe sync state tracking
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
                'active_count': sum(1 for db in remote_dbs if db.is_active),
                'last_sync': None,
                'local_available': cls._check_local_db_exists()
            }
            
            for db in remote_dbs:
                try:
                    storage = LibSQLStorage(url=db.url)
                    task_count = storage.get_task_count()
                    
                    status['connected_dbs'].append({
                        'id': db.id,
                        'name': db.name,
                        'url': db.url,
                        'status': 'connected' if db.is_active else 'inactive',
                        'task_count': task_count,
                        'last_synced': db.last_synced_at,
                        'auto_sync': db.auto_sync
                    })
                    
                    if db.last_synced_at and not status['last_sync']:
                        status['last_sync'] = db.last_synced_at
                    
                    storage.close()
                    
                except Exception as e:
                    status['connected_dbs'].append({
                        'id': db.id,
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
                'active_count': 0,
                'local_available': cls._check_local_db_exists()
            }
    
    @classmethod
    def _check_local_db_exists(cls) -> bool:
        """Check if local SQLite database exists."""
        try:
            from gtasks_cli.storage.sqlite_storage import SQLiteStorage
            storage = SQLiteStorage()
            # Try to load tasks to verify connection
            tasks = storage.load_tasks()
            return True
        except Exception:
            return False
    
    @classmethod
    def add_remote_db(cls, url: str, name: str = None, token: str = None) -> Dict[str, Any]:
        """Add a new remote database."""
        try:
            from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager
            
            manager = RemoteSyncManager()
            result = manager.add_remote_db(url=url, name=name, token=token)
            
            return {
                'success': result.success,
                'message': result.message,
                'config': result.details.get('config') if result.success else None,
                'task_count': result.details.get('task_count') if result.success else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def remove_remote_db(cls, url: str) -> Dict[str, Any]:
        """Remove a remote database."""
        try:
            from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager
            
            manager = RemoteSyncManager()
            result = manager.remove_remote_db(url)
            
            return {
                'success': result.success,
                'message': result.message
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
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
            result = manager.sync_all(push_to_remote=True, sync_with_google=False)
            
            with cls._state_lock:
                if sync_id in cls._sync_state:
                    if result.success:
                        cls._sync_state[sync_id].update({
                            'progress': 100,
                            'message': 'Sync completed successfully',
                            'status': 'completed',
                            'result': result.to_dict()
                        })
                    else:
                        cls._sync_state[sync_id].update({
                            'progress': 0,
                            'message': f"Sync failed: {result.message}",
                            'status': 'error',
                            'error': result.message
                        })
                        
        except Exception as e:
            import traceback
            with cls._state_lock:
                if sync_id in cls._sync_state:
                    cls._sync_state[sync_id].update({
                        'progress': 0,
                        'message': f"Sync error: {str(e)}",
                        'status': 'error',
                        'error': str(e),
                        'traceback': traceback.format_exc()
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
    
    @classmethod
    def preview_sync(cls) -> Dict[str, Any]:
        """Preview sync changes."""
        try:
            from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager
            
            manager = RemoteSyncManager()
            preview = manager.preview_sync()
            
            return {
                'success': True,
                'preview': preview
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def load_tasks_from_remote(cls, db_url: str = None) -> Dict[str, Any]:
        """
        Load tasks from remote database, falling back to local if needed.
        This is used when local DB doesn't exist.
        """
        try:
            # If local DB exists, use it
            if cls._check_local_db_exists():
                return {
                    'source': 'local',
                    'message': 'Using local database'
                }
            
            # Try remote if local doesn't exist
            if db_url:
                from gtasks_cli.storage.libsql_storage import LibSQLStorage
                
                storage = LibSQLStorage(url=db_url)
                tasks = storage.load_tasks()
                storage.close()
                
                return {
                    'source': 'remote',
                    'tasks': tasks,
                    'task_count': len(tasks),
                    'message': f'Loaded {len(tasks)} tasks from remote database'
                }
            else:
                # Try first active remote DB
                from gtasks_cli.storage.sync_config_storage import SyncConfigStorage
                
                config_storage = SyncConfigStorage()
                active_dbs = config_storage.get_active_remote_dbs()
                
                if active_dbs:
                    db = active_dbs[0]
                    from gtasks_cli.storage.libsql_storage import LibSQLStorage
                    
                    storage = LibSQLStorage(url=db.url)
                    tasks = storage.load_tasks()
                    storage.close()
                    
                    return {
                        'source': 'remote',
                        'tasks': tasks,
                        'task_count': len(tasks),
                        'db_name': db.name,
                        'message': f"Loaded {len(tasks)} tasks from {db.name}"
                    }
                else:
                    return {
                        'source': 'none',
                        'message': 'No local or remote database available'
                    }
                    
        except Exception as e:
            return {
                'source': 'error',
                'error': str(e),
                'message': f'Error loading tasks: {str(e)}'
            }
    
    @classmethod
    def get_remote_db_info(cls, url: str) -> Dict[str, Any]:
        """Get detailed information about a specific remote database."""
        try:
            from gtasks_cli.storage.sync_config_storage import SyncConfigStorage
            from gtasks_cli.storage.libsql_storage import LibSQLStorage
            
            config_storage = SyncConfigStorage()
            config = config_storage.get_remote_db(url)
            
            if not config:
                return {
                    'found': False,
                    'error': 'Database not found'
                }
            
            # Try to get task count
            task_count = 0
            try:
                storage = LibSQLStorage(url=url)
                task_count = storage.get_task_count()
                storage.close()
            except Exception:
                pass
            
            return {
                'found': True,
                'config': {
                    'id': config.id,
                    'name': config.name,
                    'url': config.url,
                    'is_active': config.is_active,
                    'auto_sync': config.auto_sync,
                    'sync_frequency': config.sync_frequency,
                    'created_at': config.created_at,
                    'last_synced': config.last_synced_at
                },
                'task_count': task_count
            }
            
        except Exception as e:
            return {
                'found': False,
                'error': str(e)
            }
