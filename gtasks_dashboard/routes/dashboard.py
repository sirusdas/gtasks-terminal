"""
Dashboard Routes
"""
from flask import Blueprint, render_template, send_from_directory, Response
import base64
from routes.api import init_dashboard_state

dashboard = Blueprint('dashboard', __name__)

# Initialize dashboard state
init_dashboard_state()


@dashboard.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@dashboard.route('/favicon.ico')
def favicon():
    """Serve favicon as SVG data URI"""
    svg_favicon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <rect width="100" height="100" rx="20" fill="#3b82f6"/>
        <text x="50" y="65" font-size="50" text-anchor="middle" fill="white">✓</text>
    </svg>'''
    return Response(
        f'data:image/svg+xml;base64,{base64.b64encode(svg_favicon.encode()).decode()}',
        mimetype='image/svg+xml'
    )


@dashboard.route('/sw.js')
def service_worker():
    """Serve service worker"""
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')
