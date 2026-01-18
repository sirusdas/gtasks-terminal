#!/usr/bin/env python3
"""
GTasks Dashboard - Main Entry Point

A modular, consolidated dashboard following Single Source of Truth principles.
Features are controlled by FEATURE_FLAGS in config.py instead of duplicate files.

Run: python main_dashboard.py

Author: GTasks Dashboard Team
Date: January 12, 2026
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, redirect

# Import feature flags to display available features
from config import FEATURE_FLAGS

# Create Flask app
app = Flask(__name__,
    template_folder='templates',
    static_folder='static'
)

# Import BASE_PATH from routes
from routes.dashboard import BASE_PATH

# Register blueprints
from routes.api import api, init_dashboard_state
from routes.dashboard import dashboard

# Set URL prefix for API blueprint (routes in api.py already have /api prefix, so just use BASE_PATH)
api.url_prefix = BASE_PATH

app.register_blueprint(api)
app.register_blueprint(dashboard)

# Initialize dashboard state (load accounts and tasks)
init_dashboard_state()


# Root route - redirect to subpath or serve at root for local dev
@app.route('/')
def index():
    """Root route - serve dashboard with empty base_path for local dev"""
    from routes.dashboard import render_dashboard
    # Use empty base_path for local development (no subpath)
    return render_dashboard(view='dashboard', base_path='')


@app.route('/dashboard')
def dashboard_page_local():
    """Dashboard page - explicit route for dashboard view (local development)"""
    from routes.dashboard import render_dashboard
    return render_dashboard(view='dashboard', base_path='')


@app.route('/hierarchy')
def hierarchy_page_local():
    """Hierarchy page - shows hierarchical task visualization (local development)"""
    from routes.dashboard import render_dashboard
    return render_dashboard(view='hierarchy', base_path='')


@app.route('/tasks')
def tasks_page_local():
    """Tasks page - shows task management view (local development)"""
    from routes.dashboard import render_dashboard
    return render_dashboard(view='tasks', base_path='')


@app.route('/favicon.ico')
def favicon_local():
    """Serve favicon as SVG data URI (local development)"""
    import base64
    svg_favicon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <rect width="100" height="100" rx="20" fill="#3b82f6"/>
        <text x="50" y="65" font-size="50" text-anchor="middle" fill="white">✓</text>
    </svg>'''
    from flask import Response
    return Response(
        f'data:image/svg+xml;base64,{base64.b64encode(svg_favicon.encode()).decode()}',
        mimetype='image/svg+xml'
    )


@app.route('/sw.js')
def service_worker_local():
    """Serve service worker (local development)"""
    from flask import send_from_directory
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')


# Root API routes for local development (no subpath) - duplicates of the blueprint endpoints
from flask import jsonify, request

@app.route('/api/data')
def api_data_local():
    """Get all dashboard data (for local development without subpath)"""
    from routes.api import api_data
    return api_data()

@app.route('/api/refresh', methods=['POST'])
def api_refresh_local():
    """Refresh the dashboard cache (local development)"""
    from routes.api import api_refresh_cache
    return api_refresh_cache()

@app.route('/api/tasks')
def api_tasks_local():
    """Get tasks with optional filters (local development)"""
    from routes.api import api_tasks
    return api_tasks()

@app.route('/api/accounts')
def api_accounts_local():
    """Get all accounts (local development)"""
    from routes.api import api_accounts
    return api_accounts()

@app.route('/api/accounts/<account_id>/switch', methods=['POST'])
def switch_account_local(account_id):
    """Switch to a different account (local development)"""
    from routes.api import switch_account
    return switch_account(account_id)

@app.route('/api/stats')
def api_stats_local():
    """Get dashboard statistics (local development)"""
    from routes.api import api_stats
    return api_stats()

@app.route('/api/hierarchy')
def api_hierarchy_local():
    """Get hierarchy visualization data (local development)"""
    from routes.api import api_hierarchy
    return api_hierarchy()

@app.route('/api/hierarchy/filtered')
def api_hierarchy_filtered_local():
    """Get filtered hierarchy visualization data (local development)"""
    from routes.api import api_hierarchy_filtered
    return api_hierarchy_filtered()

@app.route('/api/tasks/<task_id>')
def get_task_local(task_id):
    """Get a specific task (local development)"""
    from routes.api import get_task
    return get_task(task_id)

@app.route('/api/health')
def api_health_local():
    """Health check (local development)"""
    from routes.api import api_health
    return api_health()

@app.route('/api/tasks/<task_id>/complete', methods=['POST'])
def api_complete_task_local(task_id):
    """Mark a task as completed (local development)"""
    from routes.api import api_complete_task
    return api_complete_task(task_id)

@app.route('/api/sync/advanced', methods=['POST'])
def api_advanced_sync_local():
    """Start an advanced sync operation (local development)"""
    from routes.api import api_advanced_sync
    return api_advanced_sync()

@app.route('/api/sync/progress')
def api_sync_progress_local():
    """Get the current sync progress (local development)"""
    from routes.api import api_sync_progress
    return api_sync_progress()

@app.route('/api/sync/complete', methods=['POST'])
def api_sync_complete_local():
    """Wait for sync to complete (local development)"""
    from routes.api import api_sync_complete
    return api_sync_complete()

@app.route('/api/sync/cancel', methods=['POST'])
def api_sync_cancel_local():
    """Cancel a running sync operation (local development)"""
    from routes.api import api_sync_cancel
    return api_sync_cancel()

@app.route('/api/sync/status')
def api_sync_status_local():
    """Get the status of sync operations (local development)"""
    from routes.api import api_sync_status
    return api_sync_status()

@app.route('/api/remote/status')
def api_remote_status_local():
    """Get the status of remote sync (local development)"""
    from routes.api import api_remote_status
    return api_remote_status()

@app.route('/api/remote/databases', methods=['GET'])
def api_remote_databases_local():
    """List all configured remote databases (local development)"""
    from routes.api import api_remote_databases
    return api_remote_databases()

@app.route('/api/remote/databases', methods=['POST'])
def api_add_remote_database_local():
    """Add a new remote database (local development)"""
    from routes.api import api_add_remote_database
    return api_add_remote_database()

@app.route('/api/remote/databases/<db_id>', methods=['DELETE'])
def api_remove_remote_database_local(db_id):
    """Remove a remote database (local development)"""
    from routes.api import api_remove_remote_database
    return api_remove_remote_database(db_id)

@app.route('/api/remote/sync', methods=['POST'])
def api_remote_sync_local():
    """Perform a full sync with remote databases (local development)"""
    from routes.api import api_remote_sync
    return api_remote_sync()

@app.route('/api/remote/push', methods=['POST'])
def api_remote_push_local():
    """Push local changes to remote databases (local development)"""
    from routes.api import api_remote_push
    return api_remote_push()

@app.route('/api/remote/pull', methods=['POST'])
def api_remote_pull_local():
    """Pull remote changes to local database (local development)"""
    from routes.api import api_remote_pull
    return api_remote_pull()


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return app.send_static_file(filename)


def get_enabled_features() -> list:
    """Get list of enabled features based on feature flags"""
    features = []
    
    # Core features
    features.append("Dashboard overview with stats")
    features.append("Hierarchical task visualization (D3.js)")
    features.append("Multi-account support")
    
    # Enhanced features (based on feature flags)
    if FEATURE_FLAGS.get('ENABLE_PRIORITY_SYSTEM', False):
        features.append("Priority system (asterisk-based calculation)")
    
    if FEATURE_FLAGS.get('ENABLE_ADVANCED_FILTERS', False):
        features.append("Advanced filters (OR/AND/NOT tag filtering)")
    
    if FEATURE_FLAGS.get('ENABLE_REPORTS', False):
        features.append("Reports system")
    
    if FEATURE_FLAGS.get('ENABLE_DELETED_TASKS', False):
        features.append("Deleted tasks management")
    
    if FEATURE_FLAGS.get('ENABLE_TASKS_DUE_TODAY', False):
        features.append("Tasks due today dashboard")
    
    if FEATURE_FLAGS.get('ENABLE_ACCOUNT_TYPE_FILTERS', False):
        features.append("Multi-select account type filters")
    
    if FEATURE_FLAGS.get('ENABLE_REALTIME_UPDATES', False):
        features.append("Realtime data updates")
    
    return features


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))  # Default to 8081
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("=" * 50)
    print("  GTasks Dashboard")
    print("  Consolidated Architecture")
    print("  Single Source of Truth")
    print("=" * 50)
    print()
    print(f"🚀 Starting server on http://{host}:{port}")
    print()
    
    print("Enabled Features:")
    for feature in get_enabled_features():
        print(f"  ✅ {feature}")
    
    print()
    print("Controls:")
    print("  - Ctrl+B: Toggle sidebar")
    print("  - ESC: Exit fullscreen")
    print()
    print("-" * 50)
    print("Feature flags can be configured in config.py")
    print("-" * 50)
    
    app.run(host=host, port=port, debug=True)
