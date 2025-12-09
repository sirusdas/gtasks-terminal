"""
Configuration management for the Google Tasks CLI application.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: str = None, account_name: str = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path: Path to config file. If None, uses default location.
            account_name: Name of the account for multi-account support.
        """
        # Check for GTASKS_CONFIG_DIR environment variable for multi-account support
        config_dir_env = os.environ.get('GTASKS_CONFIG_DIR')
        if config_dir_env:
            config_dir = Path(config_dir_env)
        else:
            # Default config location
            config_dir = Path.home() / '.gtasks'
            
            # For account-specific configs, use the account directory
            if account_name:
                config_dir = config_dir / account_name
        
        config_dir.mkdir(parents=True, exist_ok=True)
        
        if config_path is None:
            self.config_path = config_dir / 'config.yaml'
        else:
            self.config_path = Path(config_path)
            
        self.config = self._load_config()
        logger.debug(f"ConfigManager initialized with config file: {self.config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        # Default configuration
        default_config = {
            'default_tasklist': 'My Tasks',
            'date_format': '%Y-%m-%d',
            'time_format': '%H:%M',
            'display': {
                'colors': True,
                'table_style': 'simple',
                'max_width': 100
            },
            'sync': {
                'pull_range_days': 10,  # Default to 10 days
                'auto_save': True  # Default to True
            },
            'accounts': {}  # For multi-account support
        }
        
        # If config file doesn't exist, create it with default values
        if not self.config_path.exists():
            self._save_config(default_config)
            logger.info(f"Created default config file: {self.config_path}")
            return default_config
            
        # Load existing config
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            logger.debug(f"Loaded config from: {self.config_path}")
            return {**default_config, **config}  # Merge with defaults
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return default_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
        """
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            logger.debug(f"Saved config to: {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the nested key location
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        # Set the value
        config[keys[-1]] = value
        
        # Save the updated configuration
        self._save_config(self.config)
        logger.debug(f"Set config key '{key}' to '{value}'")
    
    def get_account_config(self, account_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific account.
        
        Args:
            account_name: Name of the account
            
        Returns:
            Account configuration dictionary
        """
        accounts = self.get('accounts', {})
        return accounts.get(account_name, {})
    
    def set_account_config(self, account_name: str, config: Dict[str, Any]) -> None:
        """
        Set configuration for a specific account.
        
        Args:
            account_name: Name of the account
            config: Account configuration
        """
        accounts = self.get('accounts', {})
        accounts[account_name] = config
        self.set('accounts', accounts)
    
    @staticmethod
    def get_global_config() -> 'ConfigManager':
        """
        Get the global configuration manager.
        
        Returns:
            ConfigManager: Global configuration manager
        """
        global_config_path = Path.home() / '.gtasks' / 'config.yaml'
        return ConfigManager(config_path=str(global_config_path))