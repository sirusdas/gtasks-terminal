"""
Settings Management Module for GTasks Dashboard

This module handles user settings and preferences including:
- Settings persistence and loading
- Default settings configuration
- Settings validation and updates

Author: GTasks Dashboard Team
Date: January 11, 2026
"""

import json
import os
from typing import Dict, Any


class SettingsManager:
    """Manages user settings and preferences"""
    
    def __init__(self, settings_file='dashboard_settings.json'):
        self.settings_file = settings_file
        self.default_settings = {
            'show_deleted_tasks': False,
            'theme': 'light',
            'notifications': True,
            'default_view': 'dashboard',
            'auto_refresh': True,
            'compact_view': False,
            'menu_visible': True,
            'menu_animation': True,
            'keyboard_shortcuts': True,
            'priority_system_enabled': True,
            'advanced_filters_enabled': True,
            'reports_enabled': True,
            'auto_save_interval': 300,  # 5 minutes
            'timezone': 'UTC'
        }
        self.settings = self.default_settings.copy()
        self.load_settings()
    
    def load_settings(self):
        """Load user settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self.settings.update(loaded_settings)
                print(f"✅ Loaded settings from {self.settings_file}")
            else:
                print(f"ℹ️  No settings file found, using defaults")
                self.save_settings()
        except Exception as e:
            print(f"⚠️  Error loading settings: {e}")
            print("Using default settings")
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            print(f"✅ Saved settings to {self.settings_file}")
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
    
    def get_setting(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        if key in self.default_settings:
            self.settings[key] = value
            self.save_settings()
            return True
        return False
    
    def update_settings(self, settings_dict: Dict[str, Any]):
        """Update multiple settings at once"""
        updated = False
        for key, value in settings_dict.items():
            if key in self.default_settings:
                if self.settings[key] != value:
                    self.settings[key] = value
                    updated = True
        
        if updated:
            self.save_settings()
        
        return updated
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.default_settings.copy()
        self.save_settings()
        return True
    
    def get_all_settings(self):
        """Get all current settings"""
        return self.settings.copy()
    
    def validate_setting(self, key: str, value: Any) -> bool:
        """Validate a setting value"""
        validators = {
            'theme': lambda x: x in ['light', 'dark', 'auto'],
            'default_view': lambda x: x in ['dashboard', 'list', 'calendar', 'graph'],
            'show_deleted_tasks': lambda x: isinstance(x, bool),
            'notifications': lambda x: isinstance(x, bool),
            'auto_refresh': lambda x: isinstance(x, bool),
            'compact_view': lambda x: isinstance(x, bool),
            'menu_visible': lambda x: isinstance(x, bool),
            'menu_animation': lambda x: isinstance(x, bool),
            'keyboard_shortcuts': lambda x: isinstance(x, bool),
            'priority_system_enabled': lambda x: isinstance(x, bool),
            'advanced_filters_enabled': lambda x: isinstance(x, bool),
            'reports_enabled': lambda x: isinstance(x, bool),
            'auto_save_interval': lambda x: isinstance(x, int) and x > 0,
            'timezone': lambda x: isinstance(x, str)
        }
        
        if key in validators:
            return validators[key](value)
        
        return True  # Allow unknown keys for extensibility
    
    def get_ui_settings(self):
        """Get settings formatted for UI"""
        return {
            'general': {
                'theme': self.get_setting('theme'),
                'notifications': self.get_setting('notifications'),
                'auto_refresh': self.get_setting('auto_refresh')
            },
            'dashboard': {
                'default_view': self.get_setting('default_view'),
                'compact_view': self.get_setting('compact_view'),
                'menu_visible': self.get_setting('menu_visible'),
                'menu_animation': self.get_setting('menu_animation')
            },
            'features': {
                'priority_system_enabled': self.get_setting('priority_system_enabled'),
                'advanced_filters_enabled': self.get_setting('advanced_filters_enabled'),
                'reports_enabled': self.get_setting('reports_enabled')
            },
            'tasks': {
                'show_deleted_tasks': self.get_setting('show_deleted_tasks')
            },
            'advanced': {
                'keyboard_shortcuts': self.get_setting('keyboard_shortcuts'),
                'auto_save_interval': self.get_setting('auto_save_interval'),
                'timezone': self.get_setting('timezone')
            }
        }