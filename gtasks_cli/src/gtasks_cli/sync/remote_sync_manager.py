"""
Main sync manager for coordinating sync between local, remote, and Google Tasks.
Provides bidirectional synchronization with conflict resolution.
"""
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# Add gtasks_cli to path if needed
gtasks_cli_path = Path(__file__).parent.parent
if str(gtasks_cli_path) not in sys.path:
    sys.path.insert(0, str(gtasks_cli_path))

from gtasks_cli.storage.sync_config_storage import SyncConfigStorage, RemoteDBConfig
from gtasks_cli.storage.libsql_storage import LibSQLStorage
from gtasks_cli.storage.sqlite_storage import SQLiteStorage
from gtasks_cli.sync.conflict_resolver import ConflictResolver, ConflictResolutionStrategy
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


def _get_task_signature(task: Dict[str, Any]) -> str:
    """
    Create a signature for a task dictionary.
    
    Args:
        task: Task dictionary
        
    Returns:
        Task signature string
    """
    title = task.get('title', '') or ''
    description = task.get('description', '') or ''
    notes = task.get('notes', '') or ''
    full_description = description + notes
    due_date = task.get('due', '') or ''
    status = task.get('status', '') or ''
    
    from gtasks_cli.utils.task_deduplication import create_task_signature
    return create_task_signature(
        title=title,
        description=full_description,
        created_date=due_date,  # due_date maps to created_date in signature
        status=status
    )


def _get_task_content_hash(task: Dict[str, Any]) -> str:
    """
    Create a content hash for a task (for change detection).
    Excludes sync metadata like id, last_synced_at, sync_version.
    
    Args:
        task: Task dictionary
        
    Returns:
        Content hash string
    """
    import hashlib
    import json
    
    # Create a copy without sync metadata
    content = {k: v for k, v in task.items() 
               if k not in ('id', 'last_synced_at', 'sync_version', 'source')}
    
    # Sort keys for consistent hashing
    content_str = json.dumps(content, sort_keys=True, default=str)
    return hashlib.md5(content_str.encode()).hexdigest()


def _compare_tasks_by_content(local_task: Dict[str, Any], remote_task: Dict[str, Any]) -> bool:
    """
    Compare two tasks by their content (not ID).
    
    Args:
        local_task: Local task dictionary
        remote_task: Remote task dictionary
        
    Returns:
        True if tasks have same content, False otherwise
    """
    return _get_task_content_hash(local_task) == _get_task_content_hash(remote_task)


class SyncResult:
    """Result of a sync operation."""
    
    def __init__(self, success: bool, message: str, **kwargs):
        self.success = success
        self.message = message
        self.timestamp = datetime.utcnow().isoformat()
        self.details = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'message': self.message,
            'timestamp': self.timestamp,
            **self.details
        }
    
    def __str__(self) -> str:
        return f"[{'✓' if self.success else '✗'}] {self.message}"


class RemoteSyncManager:
    """Manages bidirectional sync between local, remote, and Google Tasks."""
    
    def __init__(self, account_name: str = None, strategy: ConflictResolutionStrategy = None):
        """
        Initialize sync manager.
        
        Args:
            account_name: Account name for multi-account support
            strategy: Conflict resolution strategy (defaults to NEWEST_WINS)
        """
        self.account_name = account_name
        self.strategy = strategy or ConflictResolutionStrategy.NEWEST_WINS
        self.config_storage = SyncConfigStorage(account_name=account_name)
        self.conflict_resolver = ConflictResolver(strategy=self.strategy)
        self._sync_state = {}
        self._state_lock = threading.Lock()
        
        # Initialize local storage
        self.local_storage = SQLiteStorage(account_name=account_name)
        
        logger.info(f"RemoteSyncManager initialized for account: {account_name or 'default'}")
    
    def _get_tasks_to_push(self, local_tasks: List[Dict], remote_tasks: List[Dict], 
                          force_full: bool = False) -> tuple:
        """
        Determine which tasks need to be pushed to remote (incremental sync).
        
        For each task:
        - If task doesn't exist in remote -> push (new task)
        - If task exists in remote but content differs -> push newer version
        - If task exists in remote with same content -> skip (no change)
        
        Args:
            local_tasks: List of local tasks
            remote_tasks: List of remote tasks
            force_full: If True, push all tasks (full sync)
            
        Returns:
            Tuple of (tasks_to_push, tasks_to_pull, skipped_count)
        """
        # Build signature-to-remote-task mapping
        remote_by_signature = {}
        for task in remote_tasks:
            sig = _get_task_signature(task)
            if sig not in remote_by_signature:
                remote_by_signature[sig] = task
            else:
                # Keep the newer one
                existing = remote_by_signature[sig]
                if self._is_newer(task, existing):
                    remote_by_signature[sig] = task
        
        tasks_to_push = []
        tasks_to_pull = []
        skipped_count = 0
        
        for local_task in local_tasks:
            sig = _get_task_signature(local_task)
            
            if sig not in remote_by_signature:
                # New task - push to remote
                tasks_to_push.append(local_task)
            else:
                # Task exists in remote - check if content differs
                remote_task = remote_by_signature[sig]
                
                if _compare_tasks_by_content(local_task, remote_task):
                    # Same content - skip
                    skipped_count += 1
                else:
                    # Content differs - push newer version
                    if self._is_newer(local_task, remote_task):
                        tasks_to_push.append(local_task)
                    else:
                        # Remote is newer - pull it
                        tasks_to_pull.append(remote_task)
        
        return tasks_to_push, tasks_to_pull, skipped_count
    
    def _is_newer(self, task1: Dict, task2: Dict) -> bool:
        """
        Compare two tasks to see which is newer based on modified_at.
        
        Args:
            task1: First task
            task2: Second task
            
        Returns:
            True if task1 is newer than task2
        """
        mod1 = task1.get('modified_at', '') or ''
        mod2 = task2.get('modified_at', '') or ''
        
        if not mod1 and not mod2:
            return False
        if not mod1:
            return False
        if not mod2:
            return True
        
        try:
            # Try to parse as datetime
            from datetime import datetime
            d1 = datetime.fromisoformat(mod1.replace('Z', '+00:00'))
            d2 = datetime.fromisoformat(mod2.replace('Z', '+00:00'))
            
            # Normalize to timezone-naive for comparison
            if d1.tzinfo is not None:
                d1 = d1.replace(tzinfo=None)
            if d2.tzinfo is not None:
                d2 = d2.replace(tzinfo=None)
            
            return d1 > d2
        except (ValueError, AttributeError):
            # Fallback: compare strings
            return mod1 > mod2
    
    def add_remote_db(self, url: str, name: str = None, token: str = None, 
                      auto_sync: bool = False, sync_frequency: int = 5) -> SyncResult:
        """
        Add a new remote database configuration.
        
        Args:
            url: Turso database URL
            name: Optional friendly name
            token: Authentication token (optional, uses env var)
            auto_sync: Whether to enable automatic sync
            sync_frequency: Sync frequency in minutes
            
        Returns:
            SyncResult with success status and details
        """
        try:
            # Validate connection before adding
            validation = self.config_storage.validate_connection(url, token)
            
            if not validation['success']:
                return SyncResult(
                    success=False,
                    message=f"Failed to connect to database: {validation['error']}"
                )
            
            # Create config
            config = self.config_storage.create_default_config(url, name)
            config.auto_sync = auto_sync
            config.sync_frequency = sync_frequency
            
            # Save configuration
            self.config_storage.save_remote_db(config)
            
            logger.info(f"Added remote database: {config.name} ({config.url})")
            
            return SyncResult(
                success=True,
                message=f"Successfully added remote database: {config.name}",
                config=config.to_dict(),
                task_count=validation['task_count']
            )
            
        except Exception as e:
            logger.error(f"Failed to add remote database: {e}")
            return SyncResult(success=False, message=f"Error: {str(e)}")
    
    def list_remote_dbs(self) -> List[RemoteDBConfig]:
        """List all configured remote databases."""
        return self.config_storage.load_remote_dbs()
    
    def list_active_remote_dbs(self) -> List[RemoteDBConfig]:
        """List all active (enabled) remote databases."""
        return self.config_storage.get_active_remote_dbs()
    
    def remove_remote_db(self, url: str) -> SyncResult:
        """Remove a remote database configuration."""
        success = self.config_storage.remove_remote_db(url)
        
        if success:
            logger.info(f"Removed remote database: {url}")
            return SyncResult(success=True, message=f"Removed remote database: {url}")
        else:
            return SyncResult(success=False, message=f"Database not found: {url}")
    
    def deactivate_remote_db(self, url: str) -> SyncResult:
        """Deactivate a remote database without removing."""
        success = self.config_storage.deactivate_remote_db(url)
        
        if success:
            return SyncResult(success=True, message=f"Deactivated remote database: {url}")
        else:
            return SyncResult(success=False, message=f"Database not found: {url}")
    
    def activate_remote_db(self, url: str) -> SyncResult:
        """Activate a previously deactivated remote database."""
        success = self.config_storage.activate_remote_db(url)
        
        if success:
            return SyncResult(success=True, message=f"Activated remote database: {url}")
        else:
            return SyncResult(success=False, message=f"Database not found: {url}")
    
    def sync_all(self, push_to_remote: bool = True, 
                 sync_with_google: bool = True,
                 force_full: bool = False) -> SyncResult:
        """
        Perform full sync with all configured remote databases and Google.
        Uses signature-based deduplication to detect same tasks with different IDs.
        Implements incremental sync - only pushes changed tasks.
        
        Args:
            push_to_remote: Whether to push local changes to remote
            sync_with_google: Whether to sync with Google Tasks
            force_full: If True, do full sync (push all tasks)
            
        Returns:
            SyncResult with sync summary
        """
        sync_id = str(uuid.uuid4())
        
        try:
            logger.info("Starting full sync operation")
            
            # Load local tasks
            local_tasks = self.local_storage.load_tasks()
            logger.info(f"Loaded {len(local_tasks)} tasks from local database")
            
            # Load tasks from all active remote databases
            remote_dbs = self.list_active_remote_dbs()
            all_remote_tasks = {}
            
            for config in remote_dbs:
                try:
                    storage = LibSQLStorage(url=config.url, account_name=self.account_name)
                    remote_tasks = storage.load_tasks()
                    all_remote_tasks[config.url] = {
                        'config': config,
                        'tasks': remote_tasks,
                        'success': True
                    }
                    logger.info(f"Loaded {len(remote_tasks)} tasks from {config.name}")
                    storage.close()
                except Exception as e:
                    logger.error(f"Failed to load from {config.name}: {e}")
                    all_remote_tasks[config.url] = {
                        'config': config,
                        'tasks': [],
                        'success': False,
                        'error': str(e)
                    }
            
            # Load Google tasks if requested
            google_tasks = []
            if sync_with_google:
                try:
                    from gtasks_cli.core.task_manager import TaskManager
                    
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
            
            # Collect all remote tasks into single list
            merged_remote_tasks = []
            for remote_data in all_remote_tasks.values():
                if remote_data['success']:
                    merged_remote_tasks.extend(remote_data['tasks'])
            
            # Pre-merge deduplication for remote tasks (same source)
            merged_remote_tasks = self.conflict_resolver.merge_duplicates(merged_remote_tasks)
            logger.info(f"After remote deduplication: {len(merged_remote_tasks)} tasks")
            
            # Detect cross-source duplicates BEFORE merging
            cross_source_dupes = self.conflict_resolver.detect_duplicates(
                local_tasks + merged_remote_tasks + google_tasks
            )
            if cross_source_dupes:
                logger.info(f"Detected {len(cross_source_dupes)} cross-source duplicate tasks "
                           f"that will be merged based on signature")
            
            # Get signature-to-ID mapping for logging
            all_tasks_for_mapping = local_tasks + merged_remote_tasks + google_tasks
            signature_mapping = self.conflict_resolver.get_signature_to_id_mapping(all_tasks_for_mapping)
            if len(signature_mapping) < len(all_tasks_for_mapping):
                duplicate_count = len(all_tasks_for_mapping) - len(signature_mapping)
                logger.info(f"Found {duplicate_count} duplicate tasks across sources "
                           f"(same task with different IDs)")
            
            # Get sync report before merging
            report = self.conflict_resolver.get_sync_report(
                local_tasks, merged_remote_tasks, google_tasks
            )
            logger.info(f"Sync report: {report['total_unique_tasks']} unique task signatures, "
                       f"{report.get('cross_source_conflicts', 0)} cross-source conflicts")
            
            # Merge all tasks with conflict resolution (signature-based)
            merged_tasks = self.conflict_resolver.merge_all_tasks(
                local_tasks=local_tasks,
                remote_tasks=merged_remote_tasks,
                google_tasks=google_tasks,
                strategy=self.strategy
            )
            
            logger.info(f"Merged to {len(merged_tasks)} unique tasks with signature-based deduplication")
            
            # Save merged tasks to local
            self.local_storage.save_tasks(merged_tasks)
            logger.info("Saved merged tasks to local database")
            
            # Push to remote databases with incremental sync
            push_results = {}
            if push_to_remote:
                for config in remote_dbs:
                    try:
                        storage = LibSQLStorage(url=config.url, account_name=self.account_name)
                        
                        # Get remote tasks for this specific database
                        remote_tasks = all_remote_tasks.get(config.url, {}).get('tasks', [])
                        
                        if force_full:
                            # Full sync - push all merged tasks
                            tasks_to_push = merged_tasks
                            logger.info(f"Force full sync: pushing all {len(tasks_to_push)} tasks to {config.name}")
                        else:
                            # Incremental sync - only push changed tasks
                            tasks_to_push, tasks_to_pull, skipped = self._get_tasks_to_push(
                                merged_tasks, remote_tasks, force_full
                            )
                            
                            if tasks_to_pull:
                                # Pull newer remote tasks that we don't have
                                logger.info(f"Pulling {len(tasks_to_pull)} newer tasks from {config.name}")
                                # Add pulled tasks to merged list and save locally
                                for task in tasks_to_pull:
                                    if task not in merged_tasks:
                                        merged_tasks.append(task)
                                self.local_storage.save_tasks(merged_tasks)
                            
                            logger.info(f"Incremental sync: pushing {len(tasks_to_push)}/{len(merged_tasks)} "
                                       f"tasks to {config.name} ({skipped} unchanged)")
                        
                        if tasks_to_push:
                            storage.save_tasks(tasks_to_push)
                        
                        self.config_storage.update_last_synced(config.url)
                        
                        # Update task count
                        task_count = storage.get_task_count()
                        push_results[config.url] = {
                            'success': True,
                            'task_count': task_count,
                            'tasks_pushed': len(tasks_to_push) if force_full else len(tasks_to_push),
                            'incremental': not force_full
                        }
                        
                        logger.info(f"Synced to {config.name} ({task_count} total tasks, "
                                   f"{len(tasks_to_push)} pushed)")
                        storage.close()
                    except Exception as e:
                        logger.error(f"Failed to sync to {config.name}: {e}")
                        push_results[config.url] = {
                            'success': False,
                            'error': str(e)
                        }
            
            # Count successes and failures
            successful_pushes = sum(1 for r in push_results.values() if r.get('success'))
            failed_pushes = len(push_results) - successful_pushes
            
            return SyncResult(
                success=True,
                message=f"Sync completed: {len(merged_tasks)} tasks merged, "
                       f"{successful_pushes} remote DBs updated, {failed_pushes} failed",
                sync_id=sync_id,
                local_tasks=len(local_tasks),
                remote_dbs=len(remote_dbs),
                merged_tasks=len(merged_tasks),
                google_tasks=len(google_tasks) if sync_with_google else 0,
                push_results=push_results,
                sync_report=report,
                cross_source_duplicates=len(cross_source_dupes)
            )
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return SyncResult(
                success=False,
                message=f"Sync failed: {str(e)}",
                sync_id=sync_id,
                error=str(e)
            )
    
    def sync_with_remote(self, url: str = None, bidirectional: bool = True) -> SyncResult:
        """
        Sync with a specific remote database.
        Uses signature-based deduplication for same tasks with different IDs.
        
        Args:
            url: Specific remote DB URL (syncs all if None)
            bidirectional: Whether to sync both ways
            
        Returns:
            SyncResult with sync summary
        """
        try:
            if url:
                # Sync with specific remote DB
                config = self.config_storage.get_remote_db(url)
                if not config:
                    return SyncResult(success=False, message=f"Database not found: {url}")
                
                storage = LibSQLStorage(url=url, account_name=self.account_name)
                remote_tasks = storage.load_tasks()
                
                # Pre-merge deduplication for remote tasks
                remote_tasks = self.conflict_resolver.merge_duplicates(remote_tasks)
                
                if bidirectional:
                    # Get local tasks
                    local_tasks = self.local_storage.load_tasks()
                    
                    # Detect cross-source duplicates
                    cross_source_dupes = self.conflict_resolver.detect_duplicates(
                        local_tasks + remote_tasks
                    )
                    if cross_source_dupes:
                        logger.info(f"Detected {len(cross_source_dupes)} cross-source duplicates")
                    
                    # Merge with signature-based conflict resolution
                    merged = self.conflict_resolver.merge_all_tasks(
                        local_tasks=local_tasks,
                        remote_tasks=remote_tasks,
                        google_tasks=[]
                    )
                    
                    logger.info(f"Merged to {len(merged)} unique tasks with signature-based deduplication")
                    
                    # Push to both sides
                    self.local_storage.save_tasks(merged)
                    storage.save_tasks(merged)
                    self.config_storage.update_last_synced(url)
                    
                    return SyncResult(
                        success=True,
                        message=f"Bidirectional sync completed with {config.name}: "
                               f"{len(merged)} unique tasks",
                        task_count=len(merged),
                        cross_source_duplicates=len(cross_source_dupes)
                    )
                else:
                    # One-way sync from remote to local
                    self.local_storage.save_tasks(remote_tasks)
                    self.config_storage.update_last_synced(url)
                    
                    return SyncResult(
                        success=True,
                        message=f"Synced {len(remote_tasks)} tasks from {config.name}"
                    )
            else:
                # Sync with all active remote DBs
                return self.sync_all(push_to_remote=bidirectional, sync_with_google=False)
                
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return SyncResult(success=False, message=f"Sync failed: {str(e)}")
    
    def push_to_remote(self, url: str = None) -> SyncResult:
        """Push local changes to remote database(s)."""
        try:
            local_tasks = self.local_storage.load_tasks()
            
            if url:
                # Push to specific remote DB
                config = self.config_storage.get_remote_db(url)
                if not config:
                    return SyncResult(success=False, message=f"Database not found: {url}")
                
                storage = LibSQLStorage(url=config.url, account_name=self.account_name)
                storage.save_tasks(local_tasks)
                self.config_storage.update_last_synced(url)
                
                return SyncResult(
                    success=True,
                    message=f"Pushed {len(local_tasks)} tasks to {config.name}"
                )
            else:
                # Push to all active remote DBs
                remote_dbs = self.list_active_remote_dbs()
                results = {}
                
                for config in remote_dbs:
                    try:
                        storage = LibSQLStorage(url=config.url, account_name=self.account_name)
                        storage.save_tasks(local_tasks)
                        self.config_storage.update_last_synced(config.url)
                        results[config.url] = {'success': True}
                    except Exception as e:
                        results[config.url] = {'success': False, 'error': str(e)}
                
                successful = sum(1 for r in results.values() if r.get('success'))
                
                return SyncResult(
                    success=successful > 0,
                    message=f"Pushed to {successful}/{len(remote_dbs)} remote databases",
                    results=results
                )
                
        except Exception as e:
            return SyncResult(success=False, message=f"Push failed: {str(e)}")
    
    def pull_from_remote(self, url: str = None) -> SyncResult:
        """Pull changes from remote database(s) to local."""
        try:
            if url:
                # Pull from specific remote DB
                config = self.config_storage.get_remote_db(url)
                if not config:
                    return SyncResult(success=False, message=f"Database not found: {url}")
                
                storage = LibSQLStorage(url=config.url, account_name=self.account_name)
                remote_tasks = storage.load_tasks()
                self.local_storage.save_tasks(remote_tasks)
                
                return SyncResult(
                    success=True,
                    message=f"Pulled {len(remote_tasks)} tasks from {config.name}"
                )
            else:
                # Pull from all active remote DBs and merge
                remote_dbs = self.list_active_remote_dbs()
                all_remote_tasks = []
                
                for config in remote_dbs:
                    try:
                        storage = LibSQLStorage(url=config.url, account_name=self.account_name)
                        tasks = storage.load_tasks()
                        all_remote_tasks.extend(tasks)
                        storage.close()
                    except Exception as e:
                        logger.error(f"Failed to pull from {config.name}: {e}")
                
                # Merge duplicates
                merged = self.conflict_resolver.merge_duplicates(all_remote_tasks)
                self.local_storage.save_tasks(merged)
                
                return SyncResult(
                    success=True,
                    message=f"Pulled and merged {len(merged)} tasks from {len(remote_dbs)} databases"
                )
                
        except Exception as e:
            return SyncResult(success=False, message=f"Pull failed: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current sync status."""
        remote_dbs = self.list_remote_dbs()
        active_dbs = self.list_active_remote_dbs()
        
        local_count = len(self.local_storage.load_tasks())
        
        remote_status = []
        for config in remote_dbs:
            try:
                storage = LibSQLStorage(url=config.url, account_name=self.account_name)
                count = storage.get_task_count()
                storage.close()
                
                remote_status.append({
                    'name': config.name,
                    'url': config.url,
                    'status': 'connected' if config.is_active else 'inactive',
                    'task_count': count,
                    'last_synced': config.last_synced_at,
                    'auto_sync': config.auto_sync
                })
            except Exception as e:
                remote_status.append({
                    'name': config.name,
                    'url': config.url,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'local_tasks': local_count,
            'total_remote_dbs': len(remote_dbs),
            'active_remote_dbs': len(active_dbs),
            'remote_databases': remote_status,
            'conflict_strategy': self.strategy.value
        }
    
    def preview_sync(self) -> Dict[str, Any]:
        """
        Preview what would happen during a sync operation.
        Uses signature-based analysis.
        
        Returns:
            Dictionary with preview information
        """
        local_tasks = self.local_storage.load_tasks()
        remote_dbs = self.list_active_remote_dbs()
        
        all_remote_tasks = []
        for config in remote_dbs:
            try:
                storage = LibSQLStorage(url=config.url, account_name=self.account_name)
                tasks = storage.load_tasks()
                all_remote_tasks.extend(tasks)
                storage.close()
            except Exception as e:
                pass
        
        # Pre-merge remote duplicates
        all_remote_tasks = self.conflict_resolver.merge_duplicates(all_remote_tasks)
        
        # Get signature-based report
        report = self.conflict_resolver.get_sync_report(
            local_tasks, all_remote_tasks, []
        )
        
        # Detect cross-source duplicates using signatures
        cross_source_duplicates = self.conflict_resolver.detect_duplicates(
            all_remote_tasks + local_tasks
        )
        
        # Get signature groups
        duplicate_groups = self.conflict_resolver.get_duplicate_groups(
            all_remote_tasks + local_tasks
        )
        
        return {
            'local_tasks': len(local_tasks),
            'remote_tasks': len(all_remote_tasks),
            'unique_tasks': report['total_unique_tasks'],
            'conflicts': report['conflict_candidates'],
            'cross_source_duplicates': len(cross_source_duplicates),
            'duplicate_groups_count': len(duplicate_groups),
            'changes_if_synced': {
                'new_local_tasks': report['tasks_only_in']['remote'],
                'new_remote_tasks': report['tasks_only_in']['local'],
                'updated_tasks': report['tasks_in_multiple']['all_three'] +
                                report['tasks_in_multiple']['local_and_remote'] +
                                report['tasks_in_multiple']['local_and_google'] +
                                report.get('cross_source_conflicts', 0)
            }
        }
