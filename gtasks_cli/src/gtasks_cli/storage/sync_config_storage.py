"""
Storage for remote database configurations and sync settings.
Manages multiple remote database connections securely.
"""
import yaml
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4

from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


# Token storage file name
TURSO_TOKENS_FILE = "turso_tokens.json"


@dataclass
class RemoteDBConfig:
    """Configuration for a remote database connection."""
    id: str
    url: str
    name: str
    created_at: str
    last_synced_at: Optional[str]
    is_active: bool = True
    sync_frequency: int = 5  # minutes
    auto_sync: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemoteDBConfig':
        """Create from dictionary."""
        return cls(**data)


class SyncConfigStorage:
    """Manages remote database configurations and sync settings."""
    
    def __init__(self, account_name: str = None):
        """
        Initialize sync config storage.
        
        Args:
            account_name: Account name for multi-account support
        """
        self.account_name = account_name
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / 'remote_dbs.yaml'
        self.tokens_file = self.config_dir / TURSO_TOKENS_FILE
        self._ensure_config_dir()
    
    def _get_tokens_path(self) -> Path:
        """Get the path to the secure tokens file."""
        return self.tokens_file
    
    def _load_tokens(self) -> Dict[str, str]:
        """Load stored tokens from secure file."""
        tokens_path = self._get_tokens_path()
        if not tokens_path.exists():
            return {}
        
        try:
            with open(tokens_path, 'r') as f:
                data = json.load(f)
                return data.get('tokens', {})
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")
            return {}
    
    def _save_tokens(self, tokens: Dict[str, str]) -> None:
        """Save tokens to secure file."""
        tokens_path = self._get_tokens_path()
        try:
            # Create secure file with restricted permissions
            data = {
                'version': 1,
                'tokens': tokens,
                'updated_at': datetime.utcnow().isoformat()
            }
            with open(tokens_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set restrictive permissions (owner only)
            os.chmod(tokens_path, 0o600)
            logger.debug(f"Saved tokens to {tokens_path}")
        except Exception as e:
            logger.error(f"Error saving tokens: {e}")
            raise
    
    def save_turso_token(self, url: str, token: str) -> None:
        """
        Securely save Turso database token.
        
        Args:
            url: Database URL
            token: Authentication token
        """
        tokens = self._load_tokens()
        tokens[url] = token
        self._save_tokens(tokens)
        logger.info(f"Saved token for {url}")
    
    def get_turso_token(self, url: str) -> Optional[str]:
        """
        Retrieve saved Turso token for a database URL.
        
        Args:
            url: Database URL
            
        Returns:
            Token string if found, None otherwise
        """
        tokens = self._load_tokens()
        return tokens.get(url)
    
    def remove_turso_token(self, url: str) -> bool:
        """
        Remove saved Turso token.
        
        Args:
            url: Database URL
            
        Returns:
            True if removed, False if not found
        """
        tokens = self._load_tokens()
        if url in tokens:
            del tokens[url]
            self._save_tokens(tokens)
            logger.info(f"Removed token for {url}")
            return True
        return False
    
    def _get_config_dir(self) -> Path:
        """Get configuration directory."""
        config_dir_env = os.environ.get('GTASKS_CONFIG_DIR')
        
        if config_dir_env:
            return Path(config_dir_env)
        
        base_dir = Path.home() / '.gtasks'
        
        if self.account_name:
            return base_dir / self.account_name
        
        return base_dir
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Using config directory: {self.config_dir}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {'remote_dbs': [], 'settings': {}}
        
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {'remote_dbs': [], 'settings': {}}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {'remote_dbs': [], 'settings': {}}
    
    def _save_config(self, data: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            logger.debug(f"Saved config to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    def load_remote_dbs(self) -> List[RemoteDBConfig]:
        """
        Load all configured remote databases.
        
        Returns:
            List of RemoteDBConfig objects
        """
        config = self._load_config()
        remote_dbs = config.get('remote_dbs', [])
        
        return [
            RemoteDBConfig.from_dict(db) 
            for db in remote_dbs
        ]
    
    def save_remote_db(self, config: RemoteDBConfig) -> None:
        """
        Save or update a remote database configuration.
        
        Args:
            config: RemoteDBConfig to save
        """
        remote_dbs = self.load_remote_dbs()
        
        # Remove existing with same URL or ID
        remote_dbs = [
            db for db in remote_dbs 
            if db.url != config.url and db.id != config.id
        ]
        remote_dbs.append(config)
        
        data = {
            'remote_dbs': [db.to_dict() for db in remote_dbs],
            'settings': {
                'last_modified': datetime.utcnow().isoformat()
            }
        }
        
        self._save_config(data)
        logger.info(f"Saved remote DB config: {config.name} ({config.url})")
    
    def get_remote_db(self, url: str) -> Optional[RemoteDBConfig]:
        """
        Get a specific remote database configuration.
        
        Args:
            url: Database URL to find
            
        Returns:
            RemoteDBConfig if found, None otherwise
        """
        remote_dbs = self.load_remote_dbs()
        for db in remote_dbs:
            if db.url == url:
                return db
        return None
    
    def remove_remote_db(self, url: str) -> bool:
        """
        Remove a remote database configuration.
        
        Args:
            url: Database URL to remove
            
        Returns:
            True if removed, False if not found
        """
        remote_dbs = self.load_remote_dbs()
        original_count = len(remote_dbs)
        remote_dbs = [db for db in remote_dbs if db.url != url]
        
        if len(remote_dbs) < original_count:
            data = {
                'remote_dbs': [db.to_dict() for db in remote_dbs],
                'settings': {'last_modified': datetime.utcnow().isoformat()}
            }
            self._save_config(data)
            logger.info(f"Removed remote database: {url}")
            return True
        return False
    
    def update_last_synced(self, url: str, timestamp: str = None) -> bool:
        """
        Update last synced timestamp for a remote database.
        
        Args:
            url: Database URL to update
            timestamp: Timestamp to set (defaults to now)
            
        Returns:
            True if updated, False if not found
        """
        remote_dbs = self.load_remote_dbs()
        updated = False
        
        for db in remote_dbs:
            if db.url == url:
                db.last_synced_at = timestamp or datetime.utcnow().isoformat()
                updated = True
                break
        
        if updated:
            data = {
                'remote_dbs': [db.to_dict() for db in remote_dbs],
                'settings': {'last_modified': datetime.utcnow().isoformat()}
            }
            self._save_config(data)
        
        return updated
    
    def get_active_remote_dbs(self) -> List[RemoteDBConfig]:
        """
        Get all active (enabled) remote databases.
        
        Returns:
            List of active RemoteDBConfig objects
        """
        return [db for db in self.load_remote_dbs() if db.is_active]
    
    def deactivate_remote_db(self, url: str) -> bool:
        """
        Deactivate a remote database (disable without removing).
        
        Args:
            url: Database URL to deactivate
            
        Returns:
            True if deactivated, False if not found
        """
        remote_dbs = self.load_remote_dbs()
        updated = False
        
        for db in remote_dbs:
            if db.url == url:
                db.is_active = False
                updated = True
                break
        
        if updated:
            data = {
                'remote_dbs': [db.to_dict() for db in remote_dbs],
                'settings': {'last_modified': datetime.utcnow().isoformat()}
            }
            self._save_config(data)
        
        return updated
    
    def activate_remote_db(self, url: str) -> bool:
        """
        Activate a remote database.
        
        Args:
            url: Database URL to activate
            
        Returns:
            True if activated, False if not found
        """
        remote_dbs = self.load_remote_dbs()
        updated = False
        
        for db in remote_dbs:
            if db.url == url:
                db.is_active = True
                updated = True
                break
        
        if updated:
            data = {
                'remote_dbs': [db.to_dict() for db in remote_dbs],
                'settings': {'last_modified': datetime.utcnow().isoformat()}
            }
            self._save_config(data)
        
        return updated
    
    def validate_connection(self, url: str, token: str = None) -> Dict[str, Any]:
        """
        Validate connection to a remote database.
        
        Args:
            url: Database URL to test
            token: Optional authentication token
            
        Returns:
            Dict with 'success', 'task_count', and 'error' keys
        """
        from gtasks_cli.storage.libsql_storage import LibSQLStorage
        
        try:
            storage = LibSQLStorage(url=url, auth_token=token)
            tasks = storage.load_tasks()
            task_count = len(tasks)
            storage.close()
            
            return {
                'success': True,
                'task_count': task_count,
                'message': f"Successfully connected. Found {task_count} tasks."
            }
        except Exception as e:
            return {
                'success': False,
                'task_count': 0,
                'error': str(e)
            }
    
    def create_default_config(self, url: str, name: str = None) -> RemoteDBConfig:
        """
        Create a default configuration for a new remote database.
        
        Args:
            url: Database URL
            name: Optional friendly name
            
        Returns:
            RemoteDBConfig object
        """
        return RemoteDBConfig(
            id=str(uuid4()),
            url=url,
            name=name or f"Remote DB {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            created_at=datetime.utcnow().isoformat(),
            last_synced_at=None,
            is_active=True
        )
