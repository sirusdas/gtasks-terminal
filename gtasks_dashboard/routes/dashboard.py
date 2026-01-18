"""
Dashboard Routes
"""
from flask import Blueprint, render_template, send_from_directory, Response, request
import base64
from routes.api import init_dashboard_state

# Base path for subpath deployment
BASE_PATH = '/gtasks/gtasks-terminal/gtasks_dashboard'

dashboard = Blueprint('dashboard', __name__, url_prefix=BASE_PATH)

# Initialize dashboard state
init_dashboard_state()


def get_default_view():
    """Get default view from URL query parameter or return 'dashboard'"""
    return request.args.get('view', 'dashboard')


def get_default_account():
    """Get default account from URL query parameter"""
    return request.args.get('account', None)


def render_dashboard(view='dashboard', account=None, base_path=None):
    """Render dashboard template with view and account parameters"""
    # Use provided base_path or fall back to BASE_PATH
    path = base_path if base_path is not None else BASE_PATH
    return render_template('dashboard.html', default_view=view, default_account=account, base_path=path)


@dashboard.route('/')
def index():
    """Main dashboard page - defaults to dashboard view"""
    return render_dashboard(view='dashboard')


@dashboard.route('/dashboard')
def dashboard_page():
    """Dashboard page - explicit route for dashboard view"""
    return render_dashboard(view='dashboard')


@dashboard.route('/hierarchy')
def hierarchy_page():
    """Hierarchy page - shows hierarchical task visualization"""
    return render_dashboard(view='hierarchy')


@dashboard.route('/tasks')
def tasks_page():
    """Tasks page - shows task management view"""
    return render_dashboard(view='tasks')


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
