"""
Sync Service - Provides thread-safe sync operations with progress tracking for the dashboard.
Uses the same approach as the CLI to ensure data integrity.
"""
import threading
import uuid
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add gtasks_cli to path
gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
if str(gtasks_cli_path) not in sys.path:
    sys.path.insert(0, str(gtasks_cli_path))


class SyncService:
    """
    Thread-safe service for managing advanced sync operations with progress tracking.
    Uses the exact same approach as the CLI to ensure data integrity.
    """
    
    # Class-level state for progress tracking (thread-safe via lock)
    _sync_state: Dict[str, Dict[str, Any]] = {}
    _state_lock = threading.Lock()
    _current_sync_id: Optional[str] = None
    
    @classmethod
    def start_advanced_sync(cls, sync_type: str = 'both', account: Optional[str] = None) -> str:
        """
        Start an advanced sync operation in a background thread.
        Uses the same approach as: gtasks advanced-sync
        
        Args:
            sync_type: Type of sync - 'push', 'pull', or 'both'
            account: Optional account name to sync
            
        Returns:
            str: Unique sync ID for tracking progress
        """
        sync_id = str(uuid.uuid4())
        
        with cls._state_lock:
            # Set initial state
            cls._sync_state[sync_id] = {
                'percentage': 0,
                'message': f'Initializing {sync_type} sync...',
                'status': 'running',
                'sync_type': sync_type,
                'account': account,
                'start_time': datetime.utcnow().isoformat(),
                'error': None
            }
            cls._current_sync_id = sync_id
        
        # Start sync in background thread
        sync_thread = threading.Thread(
            target=cls._run_advanced_sync,
            args=(sync_id, sync_type, account),
            daemon=True
        )
        sync_thread.start()
        
        return sync_id
    
    @classmethod
    def _run_advanced_sync(cls, sync_id: str, sync_type: str, account: Optional[str]):
        """
        Internal method to run the advanced sync operation.
        Uses the exact same approach as the CLI command.
        
        Args:
            sync_id: Unique sync identifier
            sync_type: Type of sync - 'push', 'pull', or 'both'
            account: Optional account name
        """
        def progress_callback(percentage: int, message: str, status: str):
            """Progress callback that updates the sync state."""
            with cls._state_lock:
                if sync_id in cls._sync_state:
                    cls._sync_state[sync_id].update({
                        'percentage': percentage,
                        'message': message,
                        'status': status
                    })
        
        try:
            # Import required modules - exactly like CLI does
            from gtasks_cli.core.task_manager import TaskManager
            from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager
            from gtasks_cli.storage.config_manager import ConfigManager
            
            # Determine the account to use - exactly like CLI
            if account:
                account_name = account
            else:
                # Check default from config like CLI does
                config_manager = ConfigManager()
                account_name = config_manager.get('default_account')
            
            # Load configuration to get sync settings - exactly like CLI
            config_manager = ConfigManager(account_name=account_name)
            pull_range_days = config_manager.get('sync.pull_range_days')
            
            # Create task manager - EXACTLY like CLI does
            task_manager = TaskManager(
                use_google_tasks=True, 
                storage_backend='sqlite',  # Using SQLite like CLI
                account_name=account_name
            )
            
            # Get the Google client and storage from the task manager - EXACTLY like CLI
            google_client = task_manager.google_client
            storage = task_manager.storage
            
            # Create advanced sync manager with progress callback - EXACTLY like CLI
            sync_manager = AdvancedSyncManager(
                storage=storage, 
                google_client=google_client, 
                pull_range_days=pull_range_days,
                progress_callback=progress_callback
            )
            
            # Determine push/pull flags - exactly like CLI
            push_only = sync_type == 'push'
            pull_only = sync_type == 'pull'
            
            # Run the sync - exactly like CLI
            if push_only:
                success = sync_manager.push_to_google()
            elif pull_only:
                success = sync_manager.pull_from_google()
            else:
                success = sync_manager.sync()
            
            with cls._state_lock:
                if sync_id in cls._sync_state:
                    if success:
                        cls._sync_state[sync_id].update({
                            'percentage': 100,
                            'message': 'Sync completed successfully',
                            'status': 'completed'
                        })
                    else:
                        cls._sync_state[sync_id].update({
                            'percentage': cls._sync_state[sync_id].get('percentage', 0),
                            'message': 'Sync failed',
                            'status': 'error',
                            'error': 'Sync operation failed'
                        })
        
        except Exception as e:
            import traceback
            with cls._state_lock:
                if sync_id in cls._sync_state:
                    cls._sync_state[sync_id].update({
                        'percentage': 0,
                        'message': f'Sync error: {str(e)}',
                        'status': 'error',
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    })
    
    @classmethod
    def get_sync_progress(cls, sync_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current sync progress.
        
        Args:
            sync_id: Optional sync ID to query. If not provided, uses current sync.
            
        Returns:
            Dict with keys: percentage, message, status, sync_type, account, start_time, error
        """
        with cls._state_lock:
            if sync_id is None:
                sync_id = cls._current_sync_id
            
            if sync_id and sync_id in cls._sync_state:
                return cls._sync_state[sync_id].copy()
            else:
                return {
                    'percentage': 0,
                    'message': 'No sync in progress',
                    'status': 'idle',
                    'sync_type': None,
                    'account': None,
                    'start_time': None,
                    'error': None
                }
    
    @classmethod
    def is_sync_running(cls, sync_id: Optional[str] = None) -> bool:
        """
        Check if a sync operation is currently running.
        
        Args:
            sync_id: Optional sync ID to check. If not provided, checks current sync.
            
        Returns:
            bool: True if sync is running, False otherwise
        """
        progress = cls.get_sync_progress(sync_id)
        return progress.get('status') == 'running'
    
    @classmethod
    def wait_for_sync_completion(cls, sync_id: Optional[str] = None, timeout: float = 300.0) -> Dict[str, Any]:
        """
        Wait for a sync operation to complete.
        
        Args:
            sync_id: Optional sync ID to wait for. If not provided, waits for current sync.
            timeout: Maximum time to wait in seconds (default: 5 minutes)
            
        Returns:
            Dict with final sync status
        """
        import time
        
        if sync_id is None:
            sync_id = cls._current_sync_id
        
        if not sync_id:
            return {
                'percentage': 0,
                'message': 'No sync to wait for',
                'status': 'idle',
                'error': 'No sync ID provided'
            }
        
        start_time = time.time()
        poll_interval = 0.5  # Check every 500ms
        
        while time.time() - start_time < timeout:
            with cls._state_lock:
                if sync_id not in cls._sync_state:
                    break
                
                status = cls._sync_state[sync_id].get('status')
                if status in ('completed', 'error'):
                    return cls._sync_state[sync_id].copy()
            
            time.sleep(poll_interval)
        
        # Timeout reached
        return {
            'percentage': cls.get_sync_progress(sync_id).get('percentage', 0),
            'message': 'Sync operation timed out',
            'status': 'timeout',
            'error': f'Sync did not complete within {timeout} seconds'
        }
    
    @classmethod
    def cancel_sync(cls, sync_id: Optional[str] = None) -> bool:
        """
        Cancel a running sync operation.
        Note: This sets the status to cancelled but doesn't actually stop the thread.
        
        Args:
            sync_id: Optional sync ID to cancel. If not provided, cancels current sync.
            
        Returns:
            bool: True if sync was cancelled, False if it was already completed
        """
        with cls._state_lock:
            if sync_id is None:
                sync_id = cls._current_sync_id
            
            if sync_id and sync_id in cls._sync_state:
                status = cls._sync_state[sync_id].get('status')
                if status == 'running':
                    cls._sync_state[sync_id].update({
                        'percentage': cls._sync_state[sync_id].get('percentage', 0),
                        'message': 'Sync cancelled by user',
                        'status': 'cancelled'
                    })
                    return True
            
            return False
    
    @classmethod
    def get_all_sync_ids(cls) -> list:
        """
        Get all sync IDs tracked by the service.
        
        Returns:
            list: List of sync IDs
        """
        with cls._state_lock:
            return list(cls._sync_state.keys())
    
    @classmethod
    def cleanup_old_syncs(cls, max_age_seconds: float = 3600.0):
        """
        Remove sync records older than the specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)
        """
        import time
        
        with cls._state_lock:
            current_time = time.time()
            ids_to_remove = []
            
            for sync_id, state in cls._sync_state.items():
                start_time_str = state.get('start_time')
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str).timestamp()
                        if current_time - start_time > max_age_seconds:
                            ids_to_remove.append(sync_id)
                    except (ValueError, TypeError):
                        pass
            
            for sync_id in ids_to_remove:
                del cls._sync_state[sync_id]
        
        return len(ids_to_remove)
