"""
API Routes
"""
from flask import Blueprint, jsonify, request
from services.data_manager import DataManager

api = Blueprint('api', __name__)
data_manager = DataManager()

# In-memory state
_dashboard_state = {
    'tasks': {},
    'accounts': [],
    'current_account': None,
    'stats': {}
}


def init_dashboard_state():
    """Initialize dashboard state"""
    _dashboard_state['accounts'] = data_manager.detect_accounts()
    
    # Set first account as active
    if _dashboard_state['accounts']:
        _dashboard_state['current_account'] = _dashboard_state['accounts'][0].id
    
    # Load tasks for each account
    for account in _dashboard_state['accounts']:
        tasks = data_manager.load_tasks_for_account(account.id)
        _dashboard_state['tasks'][account.id] = [t.to_dict() for t in tasks]
        account.task_count = len(tasks)
        account.completed_count = len([t for t in tasks if t.status == 'completed'])
        account.completion_rate = (account.completed_count / account.task_count * 100) if account.task_count > 0 else 0.0


def get_current_tasks():
    """Get tasks for current account"""
    current = _dashboard_state.get('current_account')
    if current:
        return _dashboard_state['tasks'].get(current, [])
    return []


@api.route('/api/data')
def api_data():
    """Get all dashboard data"""
    current_account_id = _dashboard_state.get('current_account')
    tasks = _dashboard_state['tasks'].get(current_account_id, []) if current_account_id else []
    
    # Calculate stats for current account only
    from models.task import DashboardStats
    from models.task import Task
    task_objects = [Task.from_dict(t) for t in tasks]
    stats = DashboardStats.from_tasks(task_objects)
    
    return jsonify({
        'tasks': tasks,
        'accounts': [a.to_dict() for a in _dashboard_state['accounts']],
        'current_account': current_account_id,
        'stats': {
            'total': stats.total_tasks,
            'completed': stats.completed_tasks,
            'pending': stats.pending_tasks,
            'in_progress': stats.in_progress_tasks,
            'critical': stats.critical_tasks,
            'high': stats.high_priority_tasks,
            'overdue': stats.overdue_tasks,
            'completion_rate': stats.completion_rate
        }
    })


@api.route('/api/tasks')
def api_tasks():
    """Get tasks with optional filters"""
    tasks = get_current_tasks()
    
    # Apply filters
    status = request.args.get('status')
    priority = request.args.get('priority')
    search = request.args.get('search')
    account_id = request.args.get('account_id')
    
    if account_id and account_id in _dashboard_state['tasks']:
        tasks = _dashboard_state['tasks'][account_id]
    elif not account_id:
        tasks = get_current_tasks()
    
    if status:
        tasks = [t for t in tasks if t.get('status') == status]
    
    if priority:
        tasks = [t for t in tasks if t.get('calculated_priority') == priority]
    
    if search:
        search_lower = search.lower()
        tasks = [t for t in tasks if 
                 search_lower in t.get('title', '').lower() or
                 (t.get('description') and search_lower in t.get('description', '').lower())]
    
    return jsonify({
        'tasks': tasks,
        'total': len(tasks)
    })


@api.route('/api/accounts')
def api_accounts():
    """Get all accounts"""
    return jsonify({
        'accounts': [a.to_dict() for a in _dashboard_state['accounts']],
        'current_account': _dashboard_state.get('current_account')
    })


@api.route('/api/accounts/<account_id>/switch', methods=['POST'])
def switch_account(account_id):
    """Switch to a different account"""
    if account_id in [a.id for a in _dashboard_state['accounts']]:
        _dashboard_state['current_account'] = account_id
        
        # Load tasks for this account if not already loaded
        if account_id not in _dashboard_state['tasks']:
            tasks = data_manager.load_tasks_for_account(account_id)
            _dashboard_state['tasks'][account_id] = [t.to_dict() for t in tasks]
        
        return jsonify({
            'success': True,
            'account_id': account_id
        })
    
    return jsonify({'success': False, 'error': 'Account not found'}), 404


@api.route('/api/stats')
def api_stats():
    """Get dashboard statistics"""
    from models.task import DashboardStats, Task
    
    tasks = get_current_tasks()
    task_objects = [Task.from_dict(t) for t in tasks]
    stats = DashboardStats.from_tasks(task_objects)
    
    return jsonify({
        'total': stats.total_tasks,
        'completed': stats.completed_tasks,
        'pending': stats.pending_tasks,
        'in_progress': stats.in_progress_tasks,
        'critical': stats.critical_tasks,
        'high': stats.high_priority_tasks,
        'overdue': stats.overdue_tasks,
        'completion_rate': stats.completion_rate
    })


@api.route('/api/hierarchy')
def api_hierarchy():
    """Get hierarchy visualization data"""
    from models.task import Task
    
    tasks = get_current_tasks()
    task_objects = [Task.from_dict(t) for t in tasks]
    hierarchy_data = data_manager.get_hierarchy_data(task_objects)
    
    return jsonify(hierarchy_data)


@api.route('/api/tasks/<task_id>')
def get_task(task_id):
    """Get a specific task"""
    for account_tasks in _dashboard_state['tasks'].values():
        for task in account_tasks:
            if task.get('id') == task_id:
                return jsonify(task)
    
    return jsonify({'error': 'Task not found'}), 404


@api.route('/api/health')
def api_health():
    """Health check"""
    import datetime
    from config import FEATURE_FLAGS
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'features_enabled': FEATURE_FLAGS
    })


# ============================================
# ENHANCED API ENDPOINTS (Consolidated)
# ============================================

@api.route('/api/account-types')
def api_account_types():
    """Get all account types"""
    return jsonify({
        'success': True,
        'data': data_manager.dashboard_state.get('account_types', [])
    })


@api.route('/api/available-tags')
def api_available_tags():
    """Get all available tags"""
    return jsonify({
        'success': True,
        'data': data_manager.dashboard_state.get('available_tags', {})
    })


@api.route('/api/priority-stats')
def api_priority_stats():
    """Get priority statistics"""
    return jsonify({
        'success': True,
        'data': data_manager.dashboard_state.get('priority_stats', {})
    })


@api.route('/api/tags/parse-filter', methods=['POST'])
def api_parse_tag_filter():
    """Parse tag filter string"""
    data = request.get_json()
    tag_string = data.get('tag_string', '')
    
    parsed = data_manager.parse_tag_filter(tag_string)
    return jsonify({
        'success': True,
        'data': parsed
    })


@api.route('/api/tasks/due-today')
def api_tasks_due_today():
    """Get tasks due today"""
    due_today_tasks = data_manager.get_tasks_due_today()
    return jsonify({
        'success': True,
        'data': [t.to_dict() for t in due_today_tasks]
    })


@api.route('/api/settings', methods=['GET'])
def api_get_settings():
    """Get dashboard settings"""
    return jsonify({
        'success': True,
        'data': data_manager.dashboard_state.get('settings', {})
    })


@api.route('/api/settings', methods=['POST'])
def api_update_settings():
    """Update dashboard settings"""
    data = request.get_json()
    try:
        updated_settings = data_manager.update_settings(data)
        return jsonify({
            'success': True,
            'data': updated_settings,
            'message': 'Settings updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating settings: {str(e)}'
        }), 500


@api.route('/api/tasks/<task_id>/delete', methods=['POST'])
def api_delete_task(task_id):
    """Soft delete a task"""
    data = request.get_json() or {}
    account_id = data.get('account_id', _dashboard_state.get('current_account'))
    permanent = data.get('permanent', False)
    
    try:
        if permanent:
            success = data_manager.permanently_delete_task(task_id, account_id)
            action = 'permanently deleted'
        else:
            success = data_manager.soft_delete_task(task_id, account_id)
            action = 'deleted'
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Task {action} successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting task: {str(e)}'
        }), 500


@api.route('/api/tasks/<task_id>/restore', methods=['POST'])
def api_restore_task(task_id):
    """Restore a deleted task"""
    data = request.get_json() or {}
    account_id = data.get('account_id', _dashboard_state.get('current_account'))
    
    try:
        success = data_manager.restore_task(task_id, account_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Task restored successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error restoring task: {str(e)}'
        }), 500


@api.route('/api/deleted-tasks')
def api_deleted_tasks():
    """Get deleted tasks"""
    account_id = request.args.get('account', _dashboard_state.get('current_account'))
    
    all_tasks = _dashboard_state['tasks'].get(account_id, [])
    deleted_tasks = [t for t in all_tasks if t.get('is_deleted', False)]
    
    return jsonify({'success': True, 'data': deleted_tasks})


@api.route('/api/reports/types')
def api_report_types():
    """Get available report types"""
    return jsonify({
        'success': True,
        'data': data_manager.get_report_types()
    })


@api.route('/api/reports/generate', methods=['POST'])
def api_generate_report():
    """Generate a report"""
    data = request.get_json()
    report_type = data.get('report_type')
    filters = data.get('filters', {})
    parameters = data.get('parameters', {})
    
    if not report_type:
        return jsonify({
            'success': False,
            'message': 'Report type is required'
        }), 400
    
    try:
        # Get filtered tasks
        filtered_tasks = data_manager.get_filtered_tasks(filters)
        
        # Generate report
        report_data = data_manager.generate_report(report_type, filtered_tasks, **parameters)
        
        return jsonify({
            'success': True,
            'data': report_data,
            'message': f'Report {report_type} generated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating report: {str(e)}'
        }), 500


@api.route('/api/filter-tasks', methods=['POST'])
def api_filter_tasks():
    """Advanced task filtering"""
    data = request.get_json()
    filters = data.get('filters', {})
    
    try:
        filtered_tasks = data_manager.get_filtered_tasks(filters)
        return jsonify({
            'success': True,
            'data': [t.to_dict() for t in filtered_tasks],
            'count': len(filtered_tasks)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error filtering tasks: {str(e)}'
        }), 500


@api.route('/api/updates/last')
def api_last_update():
    """Get last update timestamp"""
    return jsonify({
        'success': True,
        'data': {
            'last_update': data_manager.dashboard_state['realtime'].get('last_update'),
            'connected': data_manager.dashboard_state['realtime'].get('connected', False)
        }
    })
