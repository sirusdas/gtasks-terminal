#!/usr/bin/env python3
"""
GTasks Dashboard - Configuration Module
Centralized configuration and constants
"""

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'port': 8081,
    'debug': False,
    'host': '0.0.0.0',
    'auto_refresh_interval': 60,  # seconds
    'max_hierarchy_tasks': 100,  # Limit for performance
    'default_theme': 'light',
    'enable_animations': True,
    'sidebar_default_visible': True
}

# ============================================
# FEATURE FLAGS - Control Enhanced Features
# ============================================
# Set these to True/False to enable/disable features
# This follows the Single Source of Truth principle
# instead of maintaining multiple dashboard files

FEATURE_FLAGS = {
    # Core Features (always enabled)
    'ENABLE_BASIC_DASHBOARD': True,
    'ENABLE_HIERARCHICAL_VIEW': True,
    
    # Enhanced Features
    'ENABLE_PRIORITY_SYSTEM': True,        # Asterisk-based priority calculation
    'ENABLE_ADVANCED_FILTERS': True,       # OR/AND/NOT tag filtering
    'ENABLE_REPORTS': True,                # Reports system integration
    'ENABLE_DELETED_TASKS': True,          # Soft delete/restore functionality
    'ENABLE_REALTIME_UPDATES': True,       # Periodic data refresh
    'ENABLE_TASKS_DUE_TODAY': True,        # Tasks due today dashboard
    'ENABLE_ACCOUNT_TYPE_FILTERS': True,   # Multi-select account type filters
    'ENABLE_SETTINGS_PERSISTENCE': True,   # User settings saved to file
    
    # UI Features
    'ENABLE_COLLAPSIBLE_MENU': True,       # Collapsible sidebar menu
    'ENABLE_KEYBOARD_SHORTCUTS': True,     # Keyboard navigation
    'ENABLE_COMPACT_VIEW': False,          # Compact task display
}

# Account Type Categorization Patterns
ACCOUNT_TYPE_PATTERNS = {
    'Work': ['work', 'office', 'business', 'company', 'job', 'professional', 'corp'],
    'Personal': ['personal', 'home', 'private', 'life', 'family', 'me'],
    'Learning': ['learning', 'study', 'education', 'course', 'training', 'book'],
    'Health': ['health', 'fitness', 'medical', 'doctor', 'gym', 'exercise'],
    'Finance': ['finance', 'money', 'bank', 'investment', 'budget', 'tax'],
    'Social': ['social', 'friends', 'family', 'event', 'party', 'meeting']
}

# Priority Colors for Visualization
PRIORITY_COLORS = {
    'critical': '#ef4444',  # Red
    'high': '#f97316',      # Orange  
    'medium': '#eab308',    # Yellow
    'low': '#6b7280'        # Gray
}

# Priority Icons for Visualization
PRIORITY_ICONS = {
    'critical': '🔥',
    'high': '⚠️',
    'medium': '📋',
    'low': '📝'
}

# Available Report Types
REPORT_TYPES = {
    'task_completion': {
        'name': 'Task Completion Report',
        'description': 'Summary of completed tasks over a specified period',
        'icon': 'fa-check-circle',
        'category': 'Performance',
        'supports_date_range': True,
    },
    'overdue_tasks': {
        'name': 'Overdue Tasks Report',
        'description': 'Detailed list of tasks that are past their due dates',
        'icon': 'fa-exclamation-triangle',
        'category': 'Analysis',
        'supports_date_range': False,
    },
    'task_distribution': {
        'name': 'Task Distribution Report',
        'description': 'Analysis of tasks by category, priority, or tags',
        'icon': 'fa-chart-pie',
        'category': 'Analytics',
        'supports_date_range': False,
    },
    'timeline': {
        'name': 'Timeline Report',
        'description': 'Visual representation of tasks completed over a specified time period',
        'icon': 'fa-timeline',
        'category': 'Visualization',
        'supports_date_range': True,
    },
    'pending_tasks': {
        'name': 'Pending Tasks Report',
        'description': 'List of all pending tasks with their due dates',
        'icon': 'fa-clock',
        'category': 'Status',
        'supports_date_range': False,
    },
}

# Enhanced category mapping configuration
CATEGORIES = {
    'Team': ['@john', '@alice', '@bob', '@mou', '@john', '@devteam', '@dev', '@team'],
    'UAT': ['#UAT', '#Testing', '#QA', '#Test', '#Validation', '#test'],
    'Production': ['#Live', '#Hotfix', '#Production', '#Deploy', '#Release', '#prod'],
    'Priority': ['#High', '#Critical', '[p1]', '[urgent]', '#P0', '#P1', '#high'],
    'Projects': ['#API', '#Frontend', '#Backend', '#Mobile', '#Web', '#Database', '#api'],
    'Status': ['#InProgress', '#Blocked', '#Done', '#Review', '#Testing', '#done'],
    'Environment': ['#Dev', '#Staging', '#Prod', '#Development', '#Production', '#dev'],
    'Type': ['#Bug', '#Feature', '#Enhancement', '#Refactor', '#Documentation', '#bug'],
    'Domain': ['#Work', '#Personal', '#Learning', '#Health', '#Finance', '#work']
}

# CSS Classes for consistent styling
CSS_CLASSES = {
    'sidebar_collapsed': 'collapsed',
    'main_content': 'main-content',
    'sidebar': 'sidebar',
    'page': 'page',
    'page_active': 'active',
    'nav_link': 'nav-link',
    'card': 'bg-white rounded-lg shadow p-6',
    'button_primary': 'bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600',
    'button_secondary': 'bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600',
    'select': 'border rounded px-3 py-2',
    'input': 'border rounded px-3 py-2',
    'status_completed': 'bg-green-100 text-green-800',
    'status_in_progress': 'bg-blue-100 text-blue-800',
    'status_pending': 'bg-gray-100 text-gray-800',
    'priority_critical': 'bg-red-200 text-red-900',
    'priority_high': 'bg-red-100 text-red-800',
    'priority_medium': 'bg-yellow-100 text-yellow-800',
    'priority_low': 'bg-green-100 text-green-800'
}

# JavaScript Constants
JS_CONSTANTS = {
    'sidebar_storage_key': 'gtasks_sidebar_visible',
    'refresh_interval': 60000,  # 60 seconds in milliseconds
    'animation_duration': 300,  # 300ms
    'toast_duration': 3000,    # 3 seconds
    'api_timeout': 10000       # 10 seconds
}

# API Endpoints
API_ENDPOINTS = {
    'dashboard': '/api/dashboard',
    'tasks': '/api/tasks',
    'accounts': '/api/accounts',
    'stats': '/api/stats',
    'hierarchy': '/api/hierarchy',
    'refresh': '/api/refresh',
    'switch_account': '/api/switch_account',
    'export': '/api/export'
}