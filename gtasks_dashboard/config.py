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