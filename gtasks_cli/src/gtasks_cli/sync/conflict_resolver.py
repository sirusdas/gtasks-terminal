"""
Conflict resolution for bidirectional sync.
Uses timestamp-based resolution with newer wins strategy.
Signature-based deduplication for tasks with same content across different IDs.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.utils.task_deduplication import create_task_signature

logger = setup_logger(__name__)


class ConflictResolutionStrategy(Enum):
    """Conflict resolution strategies."""
    NEWEST_WINS = "newest_wins"  # Most recent timestamp wins
    LOCAL_WINS = "local_wins"    # Local changes preferred
    REMOTE_WINS = "remote_wins"  # Remote changes preferred
    GOOGLE_WINS = "google_wins"  # Google Tasks is source of truth
    MANUAL = "manual"            # Require manual resolution


@dataclass
class TaskVersion:
    """Represents a task version from a specific source."""
    task_id: str
    source: str  # 'local', 'remote', 'google'
    modified_at: datetime
    data: Dict[str, Any]
    priority: int  # Higher = preferred source when timestamps equal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'source': self.source,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'priority': self.priority,
            'data': self.data
        }


class ConflictResolver:
    """Resolves conflicts between task versions from different sources."""
    
    # Source priority (higher = preferred when timestamps equal)
    # Google is source of truth, then local changes, then remote
    SOURCE_PRIORITY = {
        'google': 3,
        'local': 2,
        'remote': 1
    }
    
    def __init__(self, strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.NEWEST_WINS):
        """
        Initialize conflict resolver.
        
        Args:
            strategy: Default conflict resolution strategy
        """
        self.strategy = strategy
        logger.info(f"Conflict resolver initialized with strategy: {strategy.value}")
    
    def _get_task_signature(self, task: Dict[str, Any]) -> str:
        """
        Create a signature for a task dictionary.
        Uses created_at (stable) instead of due (changes for recurring tasks).
        
        Args:
            task: Task dictionary
            
        Returns:
            Task signature string
        """
        title = task.get('title', '') or ''
        description = task.get('description', '') or ''
        # Combine description and notes like advanced_sync_manager does
        notes = task.get('notes', '') or ''
        full_description = description + notes
        # Use created_at (stable) instead of due (changes for recurring tasks)
        created_at = task.get('created_at', '') or ''
        status = task.get('status', '') or ''
        
        return create_task_signature(
            title=title,
            description=full_description,
            created_date=created_at,
            status=status
        )
    
    def _get_task_modified_at(self, task: Dict[str, Any]) -> Optional[datetime]:
        """Get the modified_at timestamp from a task dictionary."""
        return self._parse_datetime(task.get('modified_at'))
    
    def resolve(self, versions: List[TaskVersion]) -> TaskVersion:
        """
        Resolve conflict between multiple versions of the same task.
        
        Args:
            versions: List of task versions from different sources
            
        Returns:
            The resolved task version
        """
        if len(versions) == 0:
            raise ValueError("No versions provided for conflict resolution")
        
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
            # Default to newest wins
            return self._newest_wins(versions)
    
    def _newest_wins(self, versions: List[TaskVersion]) -> TaskVersion:
        """Select the version with the newest timestamp."""
        # Sort by modified_at descending, then by priority descending
        sorted_versions = sorted(
            versions,
            key=lambda v: (
                v.modified_at if v.modified_at else datetime.min,
                self.SOURCE_PRIORITY.get(v.source, 0)
            ),
            reverse=True
        )
        
        winner = sorted_versions[0]
        logger.debug(f"Conflict resolved (newest wins): {winner.source} version selected for task {winner.task_id}")
        return winner
    
    def _source_wins(self, versions: List[TaskVersion], preferred_source: str) -> TaskVersion:
        """Select version from preferred source, or newest if not available."""
        # Try to find version from preferred source
        for version in versions:
            if version.source == preferred_source:
                logger.debug(f"Conflict resolved ({preferred_source} wins): task {version.task_id}")
                return version
        
        # Fall back to newest
        return self._newest_wins(versions)
    
    def merge_all_tasks(self, local_tasks: List[Dict[str, Any]], 
                       remote_tasks: List[Dict[str, Any]],
                       google_tasks: List[Dict[str, Any]],
                       strategy: ConflictResolutionStrategy = None) -> List[Dict[str, Any]]:
        """
        Merge tasks from all sources into a single list with conflict resolution.
        Uses signature-based grouping to detect same tasks with different IDs.
        
        Args:
            local_tasks: Tasks from local SQLite
            remote_tasks: Tasks from remote Turso
            google_tasks: Tasks from Google Tasks API
            strategy: Override resolution strategy
            
        Returns:
            Merged list of tasks with conflicts resolved
        """
        # Build task map by SIGNATURE (not just ID) to handle tasks with different IDs
        # Structure: signature -> {id: {'local': task, 'remote': task, 'google': task}}
        signature_map: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Helper to add task to signature map
        def add_task_to_signature_map(task: Dict[str, Any], source: str):
            if task is None:
                return
            signature = self._get_task_signature(task)
            task_id = task.get('id')
            
            if signature not in signature_map:
                signature_map[signature] = {}
            
            if task_id:
                signature_map[signature][task_id] = {
                    'task': task,
                    'source': source
                }
        
        # Add all tasks from all sources
        for task in local_tasks:
            add_task_to_signature_map(task, 'local')
        
        for task in remote_tasks:
            add_task_to_signature_map(task, 'remote')
        
        for task in google_tasks:
            add_task_to_signature_map(task, 'google')
        
        # Resolve conflicts for each signature group
        merged_tasks = []
        conflict_count = 0
        duplicate_count = 0
        
        for signature, id_sources in signature_map.items():
            if len(id_sources) == 0:
                continue
            
            # Collect all versions from different sources
            versions = []
            for task_id, info in id_sources.items():
                task = info['task']
                source = info['source']
                modified_at = self._get_task_modified_at(task)
                
                versions.append(TaskVersion(
                    task_id=task_id,
                    source=source,
                    modified_at=modified_at,
                    data=task,
                    priority=self.SOURCE_PRIORITY.get(source, 0)
                ))
            
            # Use provided strategy or instance default
            resolve_strategy = strategy or self.strategy
            
            if resolve_strategy == ConflictResolutionStrategy.NEWEST_WINS:
                winner = self._newest_wins(versions)
            elif resolve_strategy == ConflictResolutionStrategy.LOCAL_WINS:
                winner = self._source_wins(versions, 'local')
            elif resolve_strategy == ConflictResolutionStrategy.REMOTE_WINS:
                winner = self._source_wins(versions, 'remote')
            elif resolve_strategy == ConflictResolutionStrategy.GOOGLE_WINS:
                winner = self._source_wins(versions, 'google')
            else:
                winner = self._newest_wins(versions)
            
            # Check if there was a conflict (multiple versions from different IDs)
            if len(id_sources) > 1:
                conflict_count += 1
                duplicate_count += len(id_sources) - 1
                logger.debug(f"Conflict resolved for signature {signature[:8]}...: "
                           f"{winner.source} version chosen (winner ID: {winner.task_id})")
            
            merged_tasks.append(winner.data)
        
        logger.info(f"Merged {len(signature_map)} unique tasks from {len(local_tasks)} local, "
                   f"{len(remote_tasks)} remote, {len(google_tasks)} google sources. "
                   f"Conflicts resolved: {conflict_count}, duplicates merged: {duplicate_count}")
        
        return merged_tasks
    
    def detect_duplicates(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect potential duplicate tasks using signature-based detection.
        
        Args:
            tasks: List of tasks to check
            
        Returns:
            List of tasks that appear to be duplicates (all but first in each signature group)
        """
        # Group by signature
        signature_groups: Dict[str, List[Dict[str, Any]]] = {}
        
        for task in tasks:
            signature = self._get_task_signature(task)
            if signature not in signature_groups:
                signature_groups[signature] = []
            signature_groups[signature].append(task)
        
        # Find groups with more than one task (duplicates)
        duplicates = []
        for signature, group in signature_groups.items():
            if len(group) > 1:
                # All tasks except the first one are duplicates
                duplicates.extend(group[1:])
                logger.debug(f"Found {len(group)} tasks with same signature: "
                           f"{group[0].get('title', 'Untitled')[:30]}...")
        
        return duplicates
    
    def get_duplicate_groups(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all signature groups that contain duplicates.
        
        Args:
            tasks: List of tasks to check
            
        Returns:
            Dictionary mapping signature to list of tasks with that signature
        """
        signature_groups: Dict[str, List[Dict[str, Any]]] = {}
        
        for task in tasks:
            signature = self._get_task_signature(task)
            if signature not in signature_groups:
                signature_groups[signature] = []
            signature_groups[signature].append(task)
        
        # Return only groups with duplicates
        return {sig: tasks for sig, tasks in signature_groups.items() if len(tasks) > 1}
    
    def merge_duplicates(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge duplicate tasks using signature-based grouping.
        Keeps the most recent version based on modified_at timestamp.
        
        Args:
            tasks: List of tasks potentially containing duplicates
            
        Returns:
            List with duplicates merged
        """
        # Group by signature
        signature_groups: Dict[str, List[Dict[str, Any]]] = {}
        
        for task in tasks:
            signature = self._get_task_signature(task)
            if signature not in signature_groups:
                signature_groups[signature] = []
            signature_groups[signature].append(task)
        
        # Keep the most recent version of each unique task
        merged_tasks = []
        for signature, versions in signature_groups.items():
            if len(versions) == 1:
                merged_tasks.append(versions[0])
            else:
                # Sort by modified_at and keep newest
                sorted_versions = sorted(
                    versions,
                    key=lambda t: self._get_task_modified_at(t) or datetime.min,
                    reverse=True
                )
                merged_tasks.append(sorted_versions[0])
                logger.debug(f"Merged {len(versions)} duplicates for signature {signature[:8]}...: "
                           f"keeping '{sorted_versions[0].get('title', 'Untitled')[:30]}...'")
        
        return merged_tasks
    
    def get_signature_to_id_mapping(self, tasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Get a mapping from task signatures to their IDs.
        For tasks with same signature, returns the ID of the newest task.
        
        Args:
            tasks: List of tasks
            
        Returns:
            Dictionary mapping signature to canonical ID
        """
        # Group by signature and get the newest task's ID for each group
        signature_to_id: Dict[str, str] = {}
        
        for task in tasks:
            signature = self._get_task_signature(task)
            task_id = task.get('id')
            
            if not task_id:
                continue
            
            # If signature not seen, or this task is newer, update
            if signature not in signature_to_id:
                signature_to_id[signature] = task_id
            else:
                existing_id = signature_to_id[signature]
                existing_task = next((t for t in tasks 
                                     if t.get('id') == existing_id), None)
                
                if existing_task:
                    existing_modified = self._get_task_modified_at(existing_task)
                    task_modified = self._get_task_modified_at(task)
                    
                    if task_modified and (not existing_modified or task_modified > existing_modified):
                        signature_to_id[signature] = task_id
        
        return signature_to_id
    
    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse datetime string to datetime object and normalize to timezone-naive."""
        if not dt_str:
            return None
        
        try:
            # Handle ISO format with or without timezone
            dt_str = dt_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str)
            # Normalize to timezone-naive for comparison
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse datetime: {dt_str}")
            return None
    
    def get_sync_report(self, local_tasks: List[Dict[str, Any]], 
                       remote_tasks: List[Dict[str, Any]],
                       google_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a sync report showing what would change.
        Uses signature-based analysis to detect tasks with different IDs.
        
        Args:
            local_tasks: Current local tasks
            remote_tasks: Current remote tasks
            google_tasks: Current Google tasks
            
        Returns:
            Report dictionary with statistics
        """
        # Build signature maps for each source
        local_signatures = {self._get_task_signature(t): t for t in local_tasks if t.get('id')}
        remote_signatures = {self._get_task_signature(t): t for t in remote_tasks if t.get('id')}
        google_signatures = {self._get_task_signature(t): t for t in google_tasks if t.get('id')}
        
        all_signatures = set(local_signatures.keys()) | set(remote_signatures.keys()) | set(google_signatures.keys())
        
        # Count by source
        local_count = len(local_signatures)
        remote_count = len(remote_signatures)
        google_count = len(google_signatures)
        
        # Find unique tasks per source
        only_local = local_signatures.keys() - remote_signatures.keys() - google_signatures.keys()
        only_remote = remote_signatures.keys() - local_signatures.keys() - google_signatures.keys()
        only_google = google_signatures.keys() - local_signatures.keys() - remote_signatures.keys()
        
        # Find common tasks
        in_all = local_signatures.keys() & remote_signatures.keys() & google_signatures.keys()
        in_local_remote = (local_signatures.keys() & remote_signatures.keys()) - google_signatures.keys()
        in_local_google = (local_signatures.keys() & google_signatures.keys()) - remote_signatures.keys()
        in_remote_google = (remote_signatures.keys() & google_signatures.keys()) - local_signatures.keys()
        
        # Count tasks that exist in multiple sources with different IDs
        cross_source_conflicts = 0
        for sig in all_signatures:
            sources_with_sig = []
            if sig in local_signatures:
                sources_with_sig.append('local')
            if sig in remote_signatures:
                sources_with_sig.append('remote')
            if sig in google_signatures:
                sources_with_sig.append('google')
            
            if len(sources_with_sig) > 1:
                cross_source_conflicts += 1
        
        return {
            'total_unique_tasks': len(all_signatures),
            'tasks_by_source': {
                'local': local_count,
                'remote': remote_count,
                'google': google_count
            },
            'tasks_only_in': {
                'local': len(only_local),
                'remote': len(only_remote),
                'google': len(only_google)
            },
            'tasks_in_multiple': {
                'all_three': len(in_all),
                'local_and_remote': len(in_local_remote),
                'local_and_google': len(in_local_google),
                'remote_and_google': len(in_remote_google)
            },
            'cross_source_conflicts': cross_source_conflicts,
            'conflict_candidates': len(in_all) + len(in_local_remote) + len(in_local_google) + len(in_remote_google) + cross_source_conflicts
        }
