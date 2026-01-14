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

from flask import Flask

# Import feature flags to display available features
from config import FEATURE_FLAGS

# Create Flask app
app = Flask(__name__,
    template_folder='templates',
    static_folder='static'
)

# Register blueprints
from routes.api import api, init_dashboard_state
from routes.dashboard import dashboard

app.register_blueprint(api)
app.register_blueprint(dashboard)

# Initialize dashboard state (load accounts and tasks)
init_dashboard_state()


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
