"""
API Routes
"""
from flask import Blueprint, jsonify, request
from services.data_manager import DataManager
import threading
import traceback

api = Blueprint('api', __name__)
data_manager = DataManager()

# In-memory state
_dashboard_state = {
    'tasks': {},
    'accounts': [],
    'current_account': None,
    'stats': {}
}

# Background sync lock to prevent concurrent Google sync
_sync_lock = threading.Lock()


def _sync_task_to_google_background(task_id: str, account_id: str):
    """Background task to sync task completion to Google Tasks (non-blocking)"""
    with _sync_lock:
        try:
            print(f'[Background Sync] Starting sync for task {task_id} (account: {account_id})')
            
            # Import here to avoid circular imports and only load when needed
            import sys
            from pathlib import Path
            from datetime import datetime
            
            # Add gtasks_cli to path
            gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
            if str(gtasks_cli_path) not in sys.path:
                sys.path.insert(0, str(gtasks_cli_path))
            
            from gtasks_cli.core.task_manager import TaskManager
            from gtasks_cli.storage.sqlite_storage import SQLiteStorage
            from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
            from gtasks_cli.models.task import TaskStatus
            
            # Initialize components
            storage = SQLiteStorage(account_name=account_id)
            google_client = GoogleTasksClient(account_name=account_id)
            
            # Connect to Google Tasks (non-blocking, uses cached credentials)
            if not google_client.connect(interactive=False):
                print(f'[Background Sync] Failed to connect to Google Tasks - credentials may need refresh')
                return
            
            # Get the task from local storage
            task_dicts = storage.load_tasks()
            task = None
            for t in task_dicts:
                if t.get('id') == task_id:
                    task = t
                    break
            
            if not task:
                print(f'[Background Sync] Task {task_id} not found in local storage')
                return
            
            # Create Task object
            from gtasks_cli.models.task import Task
            task_obj = Task(**task)
            
            # Update status to completed
            task_obj.status = TaskStatus.COMPLETED
            task_obj.completed_at = datetime.utcnow()
            task_obj.modified_at = datetime.utcnow()
            
            # Try to update via Google Tasks API
            try:
                if hasattr(task_obj, 'tasklist_id') and task_obj.tasklist_id:
                    updated = google_client.update_task(task_obj, task_obj.tasklist_id)
                    if updated:
                        print(f'[Background Sync] ✅ Successfully synced task {task_id} to Google Tasks')
                    else:
                        print(f'[Background Sync] ⚠️ Google Tasks API returned empty response for {task_id}')
                else:
                    print(f'[Background Sync] ⚠️ Task {task_id} has no tasklist_id, cannot sync to Google')
            except Exception as e:
                error_msg = str(e)
                if 'invalid_grant' in error_msg.lower() or 'credentials' in error_msg.lower():
                    print(f'[Background Sync] 🔑 Google credentials need refresh - sync pending')
                else:
                    print(f'[Background Sync] ❌ Error syncing to Google: {e}')
                    
        except Exception as e:
            print(f'[Background Sync] ❌ Unexpected error: {e}')
            traceback.print_exc()


def _sync_task_to_turso_background(task_id: str, account_id: str):
    """Background task to sync task completion to Turso Remote DB (non-blocking)"""
    try:
        print(f'[Turso Background Sync] Starting sync for task {task_id} (account: {account_id})')
        
        # Import required modules
        import sys
        from pathlib import Path
        
        # Add gtasks_cli to path
        gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
        if str(gtasks_cli_path) not in sys.path:
            sys.path.insert(0, str(gtasks_cli_path))
        
        from gtasks_cli.storage.sqlite_storage import SQLiteStorage
        from gtasks_cli.storage.sync_config_storage import SyncConfigStorage
        from gtasks_cli.storage.libsql_storage import LibSQLStorage
        
        # Initialize storage and load the task
        storage = SQLiteStorage(account_name=account_id)
        task_dicts = storage.load_tasks()
        task = None
        for t in task_dicts:
            if t.get('id') == task_id:
                task = t
                break
        
        if not task:
            print(f'[Turso Background Sync] Task {task_id} not found in local storage')
            return
        
        # Get active remote databases
        config_storage = SyncConfigStorage(account_name=account_id)
        active_dbs = config_storage.get_active_remote_dbs()
        
        if not active_dbs:
            print(f'[Turso Background Sync] No active remote databases configured')
            return
        
        # Push the task to each active remote DB
        for db_config in active_dbs:
            try:
                remote_storage = LibSQLStorage(url=db_config.url, account_name=account_id)
                # Get existing remote tasks
                remote_tasks = remote_storage.load_tasks()
                
                # Update or add the task
                updated_remote_tasks = []
                task_updated = False
                for rt in remote_tasks:
                    if rt.get('id') == task_id:
                        # Update existing task with completed status
                        rt['status'] = task['status']
                        rt['completed_at'] = task['completed_at']
                        rt['modified_at'] = task.get('modified_at', task['completed_at'])
                        task_updated = True
                    updated_remote_tasks.append(rt)
                
                if not task_updated:
                    # Task doesn't exist in remote, add it
                    updated_remote_tasks.append(task)
                
                # Save updated tasks
                remote_storage.save_tasks(updated_remote_tasks)
                remote_storage.close()
                
                # Update last synced timestamp
                config_storage.update_last_synced(db_config.url)
                
                print(f'[Turso Background Sync] ✅ Synced task {task_id} to {db_config.name}')
                
            except Exception as e:
                print(f'[Turso Background Sync] ❌ Error syncing to {db_config.name}: {e}')
                
    except Exception as e:
        print(f'[Turso Background Sync] ❌ Unexpected error: {e}')
        import traceback
        traceback.print_exc()


def refresh_dashboard_cache():
    """Refresh the in-memory dashboard cache from database"""
    print('[Cache] Refreshing dashboard cache...')
    _dashboard_state['accounts'] = data_manager.detect_accounts()
    
    # Try to read current account from CLI state
    import os
    from pathlib import Path
    try:
        current_account_file = Path.home() / '.gtasks' / '.current_account'
        if current_account_file.exists():
            cli_account = current_account_file.read_text().strip()
            if any(a.id == cli_account for a in _dashboard_state['accounts']):
                _dashboard_state['current_account'] = cli_account
    except Exception as e:
        print(f"Failed to read CLI current account: {e}")
        
    # Fallback to first account if not set
    if not _dashboard_state.get('current_account') and _dashboard_state['accounts']:
        _dashboard_state['current_account'] = _dashboard_state['accounts'][0].id
    
    # Load tasks for each account
    for account in _dashboard_state['accounts']:
        tasks = data_manager.load_tasks_for_account(account.id)
        _dashboard_state['tasks'][account.id] = [t.to_dict() for t in tasks]
    
    print(f'[Cache] ✅ Cache refreshed with {len(_dashboard_state.get("tasks", {}))} accounts')
    return True


def init_dashboard_state():
    """Initialize dashboard state"""
    refresh_dashboard_cache()


@api.route('/refresh', methods=['POST'])
def api_refresh_cache():
    """Refresh the dashboard cache (called when refresh button is clicked)"""
    try:
        refresh_dashboard_cache()
        return jsonify({
            'success': True,
            'message': 'Dashboard cache refreshed successfully',
            'accounts_count': len(_dashboard_state['accounts']),
            'total_tasks': sum(len(tasks) for tasks in _dashboard_state['tasks'].values())
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error refreshing cache: {str(e)}'
        }), 500


def get_current_tasks():
    """Get tasks for current account"""
    current = _dashboard_state.get('current_account')
    if current:
        return _dashboard_state['tasks'].get(current, [])
    return []


@api.route('/data')
def api_data():
    """Get all dashboard data"""
    current_account_id = _dashboard_state.get('current_account')
    tasks = _dashboard_state['tasks'].get(current_account_id, []) if current_account_id else []
    
    # Calculate stats for current account only
    from models.task import DashboardStats
    from models.task import Task
    task_objects = [Task.from_dict(t) for t in tasks]
    stats = DashboardStats.from_tasks(task_objects)
    
    # Get all unique list names from task_lists table and loaded tasks for the current account
    list_names = set()
    if current_account_id:
        try:
            from pathlib import Path
            import sqlite3
            gtasks_home = Path.home() / '.gtasks'
            db_path = gtasks_home / current_account_id / 'tasks.db'
            if not db_path.exists():
                db_path = gtasks_home / 'tasks.db'
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT DISTINCT list_name FROM task_lists WHERE list_name IS NOT NULL AND list_name != ''")
                    for row in cursor.fetchall():
                        if row[0]:
                            list_names.add(row[0])
                except Exception as e:
                    print(f"⚠️  Error loading list names: {e}")
                conn.close()
        except Exception as e:
            print(f"⚠️  Error loading list names: {e}")
            
    for t in tasks:
        lt = t.get('list_title')
        if lt:
            list_names.add(lt)

    # Get ALL Google task lists (including empty ones) via Google API for current_account_id
    all_google_lists = []
    if current_account_id:
        try:
            import sys
            from pathlib import Path
            gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
            if str(gtasks_cli_path) not in sys.path:
                sys.path.insert(0, str(gtasks_cli_path))
            from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
            google_client = GoogleTasksClient(account_name=current_account_id)
            if google_client.connect(interactive=False):
                google_lists = google_client.list_tasklists()
                for gl in google_lists:
                    all_google_lists.append({'id': gl['id'], 'title': gl['title']})
                    list_names.add(gl['title'])
        except Exception as e:
            print(f"⚠️  Error loading Google task lists for account '{current_account_id}': {e}")
    
    sorted_list_names = sorted(list(list_names))
    if not sorted_list_names:
        sorted_list_names = ['My Tasks']
        
    if not all_google_lists:
        all_google_lists = [{'id': name, 'title': name} for name in sorted_list_names]

    return jsonify({
        'tasks': tasks,
        'accounts': [a.to_dict() for a in _dashboard_state['accounts']],
        'current_account': current_account_id,
        'lists': sorted_list_names,
        'all_google_lists': all_google_lists,
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


@api.route('/tasks')
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


@api.route('/accounts')
def api_accounts():
    """Get all accounts"""
    return jsonify({
        'accounts': [a.to_dict() for a in _dashboard_state['accounts']],
        'current_account': _dashboard_state.get('current_account')
    })


@api.route('/accounts/<account_id>/switch', methods=['POST'])
def switch_account(account_id):
    """Switch to a different account"""
    if account_id in [a.id for a in _dashboard_state['accounts']]:
        _dashboard_state['current_account'] = account_id
        
        # Load tasks for this account if not already loaded
        if account_id not in _dashboard_state['tasks']:
            tasks = data_manager.load_tasks_for_account(account_id)
            _dashboard_state['tasks'][account_id] = [t.to_dict() for t in tasks]
            
        # Synchronize with CLI state
        import os
        from pathlib import Path
        try:
            current_account_file = Path.home() / '.gtasks' / '.current_account'
            current_account_file.write_text(account_id)
        except Exception as e:
            print(f"Failed to write current account to CLI file: {e}")
        
        return jsonify({
            'success': True,
            'account_id': account_id
        })
    
    return jsonify({'success': False, 'error': 'Account not found'}), 404


@api.route('/accounts/create', methods=['POST'])
def api_create_account():
    """Create a new account (defaults to 'Personal' if no name provided)"""
    data = request.get_json() or {}
    account_name = data.get('name')  # None if not provided
    
    try:
        # Use AccountManager to create the account
        from modules.account_manager import AccountManager
        account_manager = AccountManager()
        
        result = account_manager.create_account(account_name)
        
        if result.get('success'):
            # Refresh dashboard cache to include new account
            refresh_dashboard_cache()
            
            return jsonify({
                'success': True,
                'account': result.get('account'),
                'message': f"Account '{account_name or 'Personal'}' created and set as current"
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to create account')
            }), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error creating account: {str(e)}'
        }), 500


@api.route('/stats')
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


@api.route('/hierarchy')
def api_hierarchy():
    """Get hierarchy visualization data"""
    from models.task import Task
    
    tasks = get_current_tasks()
    task_objects = [Task.from_dict(t) for t in tasks]
    hierarchy_data = data_manager.get_hierarchy_data(task_objects)
    
    return jsonify(hierarchy_data)


@api.route('/hierarchy/filtered')
def api_hierarchy_filtered():
    """Get filtered hierarchy visualization data"""
    from models.task import Task
    
    # Get filter parameters
    tag_search = request.args.get('tag_search', '')
    status = request.args.get('status', '')
    date_field = request.args.get('date_field', 'due')
    date_start = request.args.get('date_start', '')
    date_end = request.args.get('date_end', '')
    
    # Parse tag search (comma-separated)
    tag_filters = data_manager.parse_chart_tag_filter(tag_search)
    
    tasks = get_current_tasks()
    task_objects = [Task.from_dict(t) for t in tasks]
    
    # Get filtered hierarchy data
    if tag_filters or status or date_start or date_end:
        hierarchy_data = data_manager.get_filtered_hierarchy_data(
            task_objects,
            tag_filters=tag_filters,
            status_filter=status or None,
            date_field=date_field,
            date_start=date_start or None,
            date_end=date_end or None
        )
    else:
        hierarchy_data = data_manager.get_hierarchy_data(task_objects)
    
    return jsonify(hierarchy_data)


@api.route('/tasks/<task_id>')
def get_task(task_id):
    """Get a specific task"""
    for account_tasks in _dashboard_state['tasks'].values():
        for task in account_tasks:
            if task.get('id') == task_id:
                return jsonify(task)
    
    return jsonify({'error': 'Task not found'}), 404


@api.route('/tasks', methods=['POST'])
def api_create_task():
    """Create a new task in local DB and sync immediately to Google Tasks & Turso"""
    import uuid
    from datetime import datetime

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'Title is required'}), 400

    account_id = data.get('account_id', _dashboard_state.get('current_account'))
    if not account_id or account_id not in _dashboard_state.get('tasks', {}):
        account_id = _dashboard_state.get('current_account') or (list(_dashboard_state['tasks'].keys())[0] if _dashboard_state.get('tasks') else 'default')

    list_title = data.get('list_title', 'My Tasks')
    priority = data.get('priority', 'medium')
    status = data.get('status', 'pending')
    due = data.get('due', None)
    notes = data.get('notes', '')

    import re
    import json
    raw_tags = re.findall(r'\[([^\]\r\n]+)\](?!\()', f"{title} {notes}")
    extracted_tags = [t.strip().lower() for t in raw_tags if t.strip() and len(t.strip()) <= 40 and not any(c in t for c in '{}"\':,\r\n\t')]

    task_id = str(uuid.uuid4())
    now_iso = datetime.now().isoformat()

    new_task = {
        'id': task_id,
        'title': title,
        'notes': notes,
        'description': notes,
        'priority': priority,
        'calculated_priority': priority,
        'status': status,
        'due': due,
        'list_title': list_title,
        'account_id': account_id,
        'created_at': now_iso,
        'modified_at': now_iso,
        'tags': extracted_tags,
        'dependencies': []
    }

    # Save to local SQLite database
    try:
        import sqlite3
        from pathlib import Path
        gtasks_home = Path.home() / '.gtasks'
        db_path = gtasks_home / account_id / 'tasks.db'
        if not db_path.exists():
            db_path = gtasks_home / 'tasks.db'

        if db_path and db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check table schema for list_title and tags
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [col[1] for col in cursor.fetchall()]

            tags_json = json.dumps(extracted_tags)
            if 'list_title' in columns:
                cursor.execute("""
                    INSERT INTO tasks (id, title, description, notes, priority, status, due, tags, created_at, modified_at, list_title)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (task_id, title, notes, notes, priority, status, due, tags_json, now_iso, now_iso, list_title))
            else:
                cursor.execute("""
                    INSERT INTO tasks (id, title, description, notes, priority, status, due, tags, created_at, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (task_id, title, notes, notes, priority, status, due, tags_json, now_iso, now_iso))

            cursor.execute("INSERT INTO task_lists (task_id, list_name) VALUES (?, ?)", (task_id, list_title))

            conn.commit()
            conn.close()
            print(f'[API] Task {task_id} created in local DB for account {account_id}')
    except Exception as e:
        print(f'[API] Error saving new task to local DB: {e}')

    # Add to memory cache
    _dashboard_state['current_account'] = account_id
    try:
        from pathlib import Path
        current_account_file = Path.home() / '.gtasks' / '.current_account'
        current_account_file.write_text(account_id)
    except Exception as e:
        print(f"Failed to update current account file: {e}")

    if account_id not in _dashboard_state['tasks']:
        _dashboard_state['tasks'][account_id] = []
    _dashboard_state['tasks'][account_id].insert(0, new_task)

    # Immediate Sync to Google Tasks
    synced_to_google = False
    try:
        import sys
        from pathlib import Path
        gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
        if str(gtasks_cli_path) not in sys.path:
            sys.path.insert(0, str(gtasks_cli_path))

        from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
        from gtasks_cli.models.task import Task as CLITask, TaskStatus, Priority as CLIPriority

        google_client = GoogleTasksClient(account_name=account_id)
        if google_client.connect(interactive=False):
            all_lists = google_client.list_tasklists()
            target_list_id = '@default'
            for tl in all_lists:
                if tl.get('title') == list_title:
                    target_list_id = tl['id']
                    break

            cli_status = TaskStatus.COMPLETED if status == 'completed' else TaskStatus.PENDING
            cli_prio = CLIPriority.HIGH if priority == 'high' else CLIPriority.CRITICAL if priority == 'critical' else CLIPriority.MEDIUM

            cli_task = CLITask(
                id=task_id,
                title=title,
                notes=notes,
                description=notes,
                due=due,
                status=cli_status,
                priority=cli_prio,
                tasklist_id=target_list_id
            )

            created_google_task = google_client.create_task(cli_task)
            if created_google_task:
                synced_to_google = True
                print(f"[API] ✅ New task {task_id} synced immediately to Google Tasks list '{list_title}'")
    except Exception as e:
        print(f"[API] ❌ Error syncing new task to Google Tasks: {e}")

    # Immediate Sync to Turso DB
    try:
        turso_sync_thread = threading.Thread(
            target=_sync_task_to_turso_background,
            args=(task_id, account_id),
            daemon=True
        )
        turso_sync_thread.start()
    except Exception as e:
        print(f"[API] Error triggering Turso sync: {e}")

    return jsonify({'success': True, 'task': new_task, 'synced_to_google': synced_to_google})


@api.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task's title, notes, description, priority, status, list_title"""
    from datetime import datetime
    data = request.get_json() or {}
    account_id = data.get('account_id', _dashboard_state.get('current_account'))

    # Find the task
    target_task = None
    target_account = None

    accounts_to_search = [account_id] if account_id and account_id in _dashboard_state['tasks'] else list(_dashboard_state['tasks'].keys())

    for acc_id in accounts_to_search:
        for task in _dashboard_state['tasks'].get(acc_id, []):
            if task.get('id') == task_id:
                target_task = task
                target_account = acc_id
                break
        if target_task:
            break

    if not target_task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404

    old_list_title = target_task.get('list_title', 'My Tasks')

    # Synchronize description with notes and extract tags
    if 'notes' in data:
        target_task['notes'] = data['notes']
        target_task['description'] = data['notes']
    elif 'description' in data:
        target_task['notes'] = data['description']
        target_task['description'] = data['description']

    import re
    raw_tags = re.findall(r'\[([^\]\r\n]+)\](?!\()', f"{target_task.get('title', '')} {target_task.get('notes', '')}")
    extracted_tags = [t.strip().lower() for t in raw_tags if t.strip() and len(t.strip()) <= 40 and not any(c in t for c in '{}"\':,\r\n\t')]
    target_task['tags'] = extracted_tags

    target_task['modified_at'] = datetime.now().isoformat()
    new_list_title = target_task.get('list_title', old_list_title)

    # Sync to local SQLite
    db_path = None
    try:
        import sqlite3
        import json
        from pathlib import Path
        gtasks_home = Path.home() / '.gtasks'
        db_path = gtasks_home / target_account / 'tasks.db'
        if not db_path.exists():
            db_path = gtasks_home / 'tasks.db'

        if db_path and db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check table schema
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [col[1] for col in cursor.fetchall()]

            # Build dynamic UPDATE based on provided fields
            set_clauses = ['modified_at = ?']
            values = [target_task['modified_at']]

            # Explicitly sync description, notes, and tags
            if 'description' in columns:
                set_clauses.append('description = ?')
                values.append(target_task['notes'])
            if 'notes' in columns:
                set_clauses.append('notes = ?')
                values.append(target_task['notes'])
            if 'tags' in columns:
                set_clauses.append('tags = ?')
                values.append(json.dumps(extracted_tags))

            for field in ['title', 'priority', 'status', 'due', 'list_title']:
                if field in data and field in columns:
                    set_clauses.append(f'{field} = ?')
                    values.append(target_task[field])

            values.append(task_id)
            query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, values)

            # Also update task_lists if list_title changed
            if 'list_title' in data:
                cursor.execute("DELETE FROM task_lists WHERE task_id = ?", (task_id,))
                cursor.execute("INSERT INTO task_lists (task_id, list_name) VALUES (?, ?)",
                             (task_id, new_list_title))

            conn.commit()
            conn.close()
            print(f'[API] Task {task_id} updated in local DB for account {target_account}')
    except Exception as e:
        print(f'[API] Error updating local DB: {e}')

    # Immediate Sync to Google Tasks via gtasks CLI using target_account
    synced_to_google = False
    try:
        import sys
        from pathlib import Path
        gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
        if str(gtasks_cli_path) not in sys.path:
            sys.path.insert(0, str(gtasks_cli_path))

        from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
        google_client = GoogleTasksClient(account_name=target_account)
        if google_client.connect(interactive=False):
            all_lists = google_client.list_tasklists()
            new_list_id = '@default'
            for tl in all_lists:
                if tl.get('title') == new_list_title:
                    new_list_id = tl['id']
                    break

            from gtasks_cli.models.task import Task as CLITask, TaskStatus, Priority as CLIPriority

            status_val = target_task.get('status', 'pending')
            cli_status = TaskStatus.COMPLETED if status_val == 'completed' else TaskStatus.PENDING

            prio_val = target_task.get('priority', 'medium')
            cli_prio = CLIPriority.HIGH if prio_val == 'high' else CLIPriority.CRITICAL if prio_val == 'critical' else CLIPriority.MEDIUM

            task_obj = CLITask(
                id=task_id,
                title=target_task.get('title', ''),
                notes=target_task.get('notes', '') or target_task.get('description', '') or '',
                due=target_task.get('due'),
                status=cli_status,
                priority=cli_prio,
                tasklist_id=new_list_id
            )

            # If task list changed, move task (create in new list, delete from old list)
            if 'list_title' in data and old_list_title != new_list_title:
                old_list_id = '@default'
                for tl in all_lists:
                    if tl.get('title') == old_list_title:
                        old_list_id = tl['id']
                        break
                google_client.delete_task(task_id, old_list_id)
                created = google_client.create_task(task_obj)
                if created:
                    synced_to_google = True
                    print(f'[API] Task {task_id} moved from list "{old_list_title}" to "{new_list_title}" on Google Tasks')
            else:
                updated = google_client.update_task(task_obj, new_list_id)
                if updated:
                    synced_to_google = True
                    print(f'[API] Task {task_id} synced to Google Tasks in list "{new_list_title}"')
    except Exception as e:
        print(f'[API] Error syncing task update to Google Tasks: {e}')

    # Trigger background sync to Turso Remote DB
    try:
        turso_sync_thread = threading.Thread(
            target=_sync_task_to_turso_background,
            args=(task_id, target_account),
            daemon=True
        )
        turso_sync_thread.start()
    except Exception as e:
        print(f'[API] Error triggering Turso sync: {e}')

    return jsonify({'success': True, 'task': target_task, 'synced_to_google': synced_to_google})


@api.route('/health')
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

@api.route('/account-types')
def api_account_types():
    """Get all account types"""
    return jsonify({
        'success': True,
        'data': data_manager.dashboard_state.get('account_types', [])
    })


@api.route('/available-tags')
def api_available_tags():
    """Get all available tags"""
    return jsonify({
        'success': True,
        'data': data_manager.dashboard_state.get('available_tags', {})
    })


@api.route('/priority-stats')
def api_priority_stats():
    """Get priority statistics"""
    return jsonify({
        'success': True,
        'data': data_manager.dashboard_state.get('priority_stats', {})
    })


@api.route('/tags/parse-filter', methods=['POST'])
def api_parse_tag_filter():
    """Parse tag filter string"""
    data = request.get_json()
    tag_string = data.get('tag_string', '')
    
    parsed = data_manager.parse_tag_filter(tag_string)
    return jsonify({
        'success': True,
        'data': parsed
    })


@api.route('/tasks/due-today')
def api_tasks_due_today():
    """Get tasks due today"""
    due_today_tasks = data_manager.get_tasks_due_today()
    return jsonify({
        'success': True,
        'data': [t.to_dict() for t in due_today_tasks]
    })


@api.route('/settings', methods=['GET'])
def api_get_settings():
    """Get dashboard settings"""
    return jsonify({
        'success': True,
        'data': data_manager.dashboard_state.get('settings', {})
    })


@api.route('/settings', methods=['POST'])
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


@api.route('/tasks/<task_id>/delete', methods=['POST'])
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


@api.route('/tasks/<task_id>/restore', methods=['POST'])
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


@api.route('/deleted-tasks')
def api_deleted_tasks():
    """Get deleted tasks"""
    account_id = request.args.get('account', _dashboard_state.get('current_account'))
    
    all_tasks = _dashboard_state['tasks'].get(account_id, [])
    deleted_tasks = [t for t in all_tasks if t.get('is_deleted', False)]
    
    return jsonify({'success': True, 'data': deleted_tasks})


@api.route('/reports/types')
def api_report_types():
    """Get available report types"""
    return jsonify({
        'success': True,
        'data': data_manager.get_report_types()
    })


@api.route('/reports/generate', methods=['POST'])
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


@api.route('/filter-tasks', methods=['POST'])
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


@api.route('/updates/last')
def api_last_update():
    """Get last update timestamp"""
    return jsonify({
        'success': True,
        'data': {
            'last_update': data_manager.dashboard_state['realtime'].get('last_update'),
            'connected': data_manager.dashboard_state['realtime'].get('connected', False)
        }
    })


@api.route('/tasks/<task_id>/complete', methods=['POST'])
def api_complete_task(task_id):
    """Mark a task as completed with background sync to Google Tasks"""
    from datetime import datetime
    data = request.get_json() or {}
    account_id = data.get('account_id', _dashboard_state.get('current_account'))
    sync_to_google = data.get('sync_to_google', True)
    
    print(f'[API] Completing task: {task_id}')
    print(f'[API] Account: {account_id}')
    print(f'[API] Sync to Google: {sync_to_google}')
    
    # Search in the specified account first, then all accounts
    accounts_to_search = []
    if account_id and account_id in _dashboard_state['tasks']:
        accounts_to_search = [account_id]
    else:
        accounts_to_search = list(_dashboard_state['tasks'].keys())
    
    task_found = False
    completed_task = None
    
    for acc_id in accounts_to_search:
        tasks = _dashboard_state['tasks'].get(acc_id, [])
        
        for task in tasks:
            if task.get('id') == task_id:
                print(f'[API] Found task: {task_id}')
                task_found = True
                
                # Update task in memory
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                completed_task = task
                
                # Sync to local SQLite database
                try:
                    db_path = data_manager.gtasks_path / acc_id / 'tasks.db' if data_manager.gtasks_path else None
                    if not db_path or not db_path.exists():
                        db_path = data_manager.gtasks_path / 'tasks.db' if data_manager.gtasks_path else None
                    
                    if db_path and db_path.exists():
                        import sqlite3
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE tasks 
                            SET status = ?, completed_at = ?, modified_at = ?
                            WHERE id = ?
                        """, (
                            'completed',
                            task['completed_at'],
                            datetime.now().isoformat(),
                            task_id
                        ))
                        conn.commit()
                        conn.close()
                        print(f'[API] Task {task_id} updated in local database')
                except Exception as e:
                    print(f'[API] Error updating local database: {e}')
                
                # Trigger background sync to Google Tasks (non-blocking)
                if sync_to_google:
                    print(f'[API] Starting background sync to Google Tasks...')
                    sync_thread = threading.Thread(
                        target=_sync_task_to_google_background,
                        args=(task_id, acc_id),
                        daemon=True
                    )
                    sync_thread.start()
                    print(f'[API] Background sync thread started for task {task_id}')
                
                # Trigger background sync to Turso Remote DB (non-blocking)
                print(f'[API] Starting background sync to Turso Remote DB...')
                turso_sync_thread = threading.Thread(
                    target=_sync_task_to_turso_background,
                    args=(task_id, acc_id),
                    daemon=True
                )
                turso_sync_thread.start()
                print(f'[API] Background Turso sync thread started for task {task_id}')
                
                break
        
        if task_found:
            break
    
    if task_found:
        return jsonify({
            'success': True,
            'message': 'Task completed successfully',
            'syncing': sync_to_google
        })
    else:
        print(f'[API] Task {task_id} not found')
        return jsonify({
            'success': False,
            'message': 'Task not found'
        }), 404


# ============================================
# ADVANCED SYNC ENDPOINTS
# ============================================

@api.route('/sync/advanced', methods=['POST'])
def api_advanced_sync():
    """
    Start an advanced sync operation.
    
    Request body:
        {
            "sync_type": "push|pull|both" (default: "both"),
            "account": "optional_account_name"
        }
        
    Response:
        {
            "success": True,
            "sync_id": "unique_sync_id",
            "message": "Sync started"
        }
    """
    from services.sync_service import SyncService
    
    try:
        data = request.get_json() or {}
        sync_type = data.get('sync_type', 'both')
        account = data.get('account')
        
        if not account:
            account = _dashboard_state.get('current_account')
            

        # Validate sync_type
        if sync_type not in ('push', 'pull', 'both'):
            return jsonify({
                'success': False,
                'message': 'Invalid sync_type. Must be "push", "pull", or "both"'
            }), 400
        
        # Start the sync
        sync_id = SyncService.start_advanced_sync(sync_type=sync_type, account=account)
        
        return jsonify({
            'success': True,
            'sync_id': sync_id,
            'message': f'Started {sync_type} sync'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting sync: {str(e)}'
        }), 500


@api.route('/sync/progress')
def api_sync_progress():
    """
    Get the current sync progress.
    
    Query parameters:
        sync_id: Optional sync ID to query (uses current sync if not provided)
        
    Response:
        {
            "success": True,
            "data": {
                "percentage": 0-100,
                "message": "description",
                "status": "running|completed|error|idle",
                "sync_type": "push|pull|both",
                "account": "account_name",
                "start_time": "ISO timestamp",
                "error": "error message if any"
            }
        }
    """
    from services.sync_service import SyncService
    
    try:
        sync_id = request.args.get('sync_id')
        progress = SyncService.get_sync_progress(sync_id=sync_id)
        
        return jsonify({
            'success': True,
            'data': progress
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting sync progress: {str(e)}'
        }), 500


@api.route('/sync/complete', methods=['POST'])
def api_sync_complete():
    """
    Wait for sync to complete and return final status.
    
    Request body:
        {
            "sync_id": "optional_sync_id",
            "timeout": 300 (optional, default 300 seconds)
        }
        
    Response:
        {
            "success": True,
            "data": {
                "percentage": 0-100,
                "message": "description",
                "status": "completed|error|timeout",
                "error": "error message if any"
            }
        }
    """
    from services.sync_service import SyncService
    
    try:
        data = request.get_json() or {}
        sync_id = data.get('sync_id')
        timeout = float(data.get('timeout', 300))
        
        result = SyncService.wait_for_sync_completion(sync_id=sync_id, timeout=timeout)
        
        # Refresh dashboard cache after sync completes
        if result.get('status') == 'completed':
            refresh_dashboard_cache()
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error waiting for sync completion: {str(e)}'
        }), 500


@api.route('/sync/cancel', methods=['POST'])
def api_sync_cancel():
    """
    Cancel a running sync operation.
    
    Request body:
        {
            "sync_id": "optional_sync_id"
        }
        
    Response:
        {
            "success": True,
            "message": "Sync cancelled"
        }
    """
    from services.sync_service import SyncService
    
    try:
        data = request.get_json() or {}
        sync_id = data.get('sync_id')
        
        cancelled = SyncService.cancel_sync(sync_id=sync_id)
        
        if cancelled:
            return jsonify({
                'success': True,
                'message': 'Sync cancelled'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No running sync to cancel'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error cancelling sync: {str(e)}'
        }), 500


@api.route('/sync/status')
def api_sync_status():
    """
    Get the status of all sync operations or check if a specific sync is running.
    
    Query parameters:
        sync_id: Optional sync ID to check
        
    Response:
        {
            "success": True,
            "data": {
                "running": True/False,
                "sync_id": "current_sync_id",
                "all_sync_ids": ["id1", "id2", ...]
            }
        }
    """
    from services.sync_service import SyncService
    
    try:
        sync_id = request.args.get('sync_id')
        is_running = SyncService.is_sync_running(sync_id=sync_id)
        
        return jsonify({
            'success': True,
            'data': {
                'running': is_running,
                'sync_id': sync_id or SyncService._current_sync_id,
                'all_sync_ids': SyncService.get_all_sync_ids()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting sync status: {str(e)}'
        }), 500


# ============================================
# REMOTE SYNC ENDPOINTS
# ============================================

@api.route('/remote/status')
def api_remote_status():
    """
    Get the status of remote sync feature.
    
    Response:
        {
            "success": True,
            "data": {
                "enabled": True/False,
                "remote_dbs": [...],
                "local_db_exists": True/False,
                "connection_status": "connected|local_only|offline",
                "last_sync": "ISO timestamp or null"
            }
        }
    """
    from services.remote_sync_service import RemoteSyncService
    
    try:
        status = RemoteSyncService.get_remote_status()
        return jsonify({
            'success': True,
            'data': status
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting remote status: {str(e)}'
        }), 500


@api.route('/remote/databases', methods=['GET'])
def api_remote_databases():
    """
    List all configured remote databases.
    
    Response:
        {
            "success": True,
            "data": [
                {
                    "id": "db_id",
                    "name": "Database Name",
                    "url": "libsql://...",
                    "active": True/False,
                    "last_sync": "ISO timestamp or null"
                },
                ...
            ]
        }
    """
    from services.remote_sync_service import RemoteSyncService
    
    try:
        databases = RemoteSyncService.list_remote_databases()
        return jsonify({
            'success': True,
            'data': databases
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error listing remote databases: {str(e)}'
        }), 500


@api.route('/remote/databases', methods=['POST'])
def api_add_remote_database():
    """
    Add a new remote database configuration.
    
    Request body:
        {
            "url": "libsql://gtaskssqllite-sirusdas.aws-ap-south-1.turso.io",
            "name": "Optional Database Name",
            "token": "optional_auth_token (or use GTASKS_TURSO_TOKEN env var)"
        }
        
    Response:
        {
            "success": True,
            "data": {
                "id": "new_db_id",
                "name": "Database Name"
            },
            "message": "Database added successfully"
        }
    """
    from services.remote_sync_service import RemoteSyncService
    
    try:
        data = request.get_json()
        url = data.get('url')
        name = data.get('name')
        token = data.get('token')
        
        if not url:
            return jsonify({
                'success': False,
                'message': 'URL is required'
            }), 400
        
        result = RemoteSyncService.add_remote_db(url, name, token)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Remote database added successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error adding remote database: {str(e)}'
        }), 500


@api.route('/remote/databases/<db_id>', methods=['DELETE'])
def api_remove_remote_database(db_id):
    """
    Remove a remote database configuration.
    
    Path parameters:
        db_id: Database ID to remove
        
    Response:
        {
            "success": True,
            "message": "Database removed successfully"
        }
    """
    from services.remote_sync_service import RemoteSyncService
    
    try:
        RemoteSyncService.remove_remote_db(db_id)
        
        return jsonify({
            'success': True,
            'message': 'Remote database removed successfully'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error removing remote database: {str(e)}'
        }), 500


@api.route('/remote/databases/<db_id>/activate', methods=['POST'])
def api_activate_remote_database(db_id):
    """
    Activate a remote database for sync.
    
    Path parameters:
        db_id: Database ID to activate
        
    Response:
        {
            "success": True,
            "message": "Database activated successfully"
        }
    """
    from services.remote_sync_service import RemoteSyncService
    
    try:
        RemoteSyncService.activate_remote_db(db_id)
        
        return jsonify({
            'success': True,
            'message': 'Remote database activated successfully'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error activating remote database: {str(e)}'
        }), 500


@api.route('/remote/databases/<db_id>/deactivate', methods=['POST'])
def api_deactivate_remote_database(db_id):
    """
    Deactivate a remote database for sync.
    
    Path parameters:
        db_id: Database ID to deactivate
        
    Response:
        {
            "success": True,
            "message": "Database deactivated successfully"
        }
    """
    from services.remote_sync_service import RemoteSyncService
    
    try:
        RemoteSyncService.deactivate_remote_db(db_id)
        
        return jsonify({
            'success': True,
            'message': 'Remote database deactivated successfully'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deactivating remote database: {str(e)}'
        }), 500


@api.route('/remote/sync', methods=['POST'])
def api_remote_sync():
    """
    Perform a full sync with all active remote databases.
    
    Request body (optional):
        {
            "push": True,  # Push local changes to remote
            "pull": True   # Pull remote changes to local
        }
        
    Response:
        {
            "success": True,
            "data": {
                "sync_id": "unique_sync_id",
                "status": "completed",
                "results": [
                    {
                        "db_id": "...",
                        "db_name": "...",
                        "pushed": 5,
                        "pulled": 3,
                        "conflicts_resolved": 2,
                        "success": True,
                        "error": null
                    },
                    ...
                ]
            },
            "message": "Sync completed successfully"
        }
    """
    from services.remote_sync_service import RemoteSyncService
    from services.sync_service import SyncService
    
    try:
        data = request.get_json() or {}
        push = data.get('push', True)
        pull = data.get('pull', True)
        
        if not push and not pull:
            return jsonify({
                'success': False,
                'message': 'At least one of push or pull must be True'
            }), 400
        
        # Start sync via SyncService for progress tracking
        sync_id = SyncService.start_advanced_sync(sync_type='both', account='remote')
        
        # Perform the actual sync
        result = RemoteSyncService.sync_all(push=pull, pull=pull)
        
        # Refresh dashboard cache after sync completes
        refresh_dashboard_cache()
        
        # Update sync status
        SyncService._sync_results[sync_id] = {
            'status': 'completed',
            'message': f'Synced with {len(result)} remote database(s)',
            'results': result
        }
        
        return jsonify({
            'success': True,
            'data': {
                'sync_id': sync_id,
                'status': 'completed',
                'results': result
            },
            'message': 'Remote sync completed successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error syncing with remote databases: {str(e)}'
        }), 500


@api.route('/remote/push', methods=['POST'])
def api_remote_push():
    """
    Push local changes to remote databases.
    
    Request body (optional):
        {
            "db_id": "specific_db_id"  # Push to specific DB, or all if not provided
        }
        
    Response:
        {
            "success": True,
            "data": {
                "results": [
                    {
                        "db_id": "...",
                        "db_name": "...",
                        "pushed": 5,
                        "success": True,
                        "error": null
                    },
                    ...
                ]
            },
            "message": "Push completed successfully"
        }
    """
    from services.remote_sync_service import RemoteSyncService
    
    try:
        data = request.get_json() or {}
        db_id = data.get('db_id')
        
        if db_id:
            result = RemoteSyncService.push_to_remote(db_id)
            results = [result]
        else:
            results = RemoteSyncService.push_all()
        
        # Refresh dashboard cache after push completes
        refresh_dashboard_cache()
        
        return jsonify({
            'success': True,
            'data': {'results': results},
            'message': 'Push to remote databases completed'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error pushing to remote databases: {str(e)}'
        }), 500


@api.route('/remote/pull', methods=['POST'])
def api_remote_pull():
    """
    Pull remote changes to local database.
    
    Request body (optional):
        {
            "db_id": "specific_db_id"  # Pull from specific DB, or all if not provided
        }
        
    Response:
        {
            "success": True,
            "data": {
                "results": [
                    {
                        "db_id": "...",
                        "db_name": "...",
                        "pulled": 3,
                        "success": True,
                        "error": null
                    },
                    ...
                ]
            },
            "message": "Pull completed successfully"
        }
    """
    from services.remote_sync_service import RemoteSyncService
    
    try:
        data = request.get_json() or {}
        db_id = data.get('db_id')
        
        if db_id:
            result = RemoteSyncService.pull_from_remote(db_id)
            results = [result]
        else:
            results = RemoteSyncService.pull_all()
        
        # Refresh dashboard cache after pull completes
        refresh_dashboard_cache()
        
        return jsonify({
            'success': True,
            'data': {'results': results},
            'message': 'Pull from remote databases completed'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error pulling from remote databases: {str(e)}'
        }), 500


@api.route('/remote/sync-command', methods=['POST'])
def api_remote_sync_command():
    """
    Execute 'gtasks remote sync' command in a background thread.
    
    This endpoint runs the CLI command and returns immediately.
    The command output will appear in the terminal where the dashboard is running.
    
    Response:
        {
            "success": True,
            "message": "Remote sync command started in background"
        }
    """
    import subprocess
    import threading
    
    try:
        def run_gtasks_remote_sync():
            """Background function to run gtasks remote sync command."""
            try:
                print('[Remote Sync] Starting gtasks remote sync...')
                result = subprocess.run(
                    ['gtasks', 'remote', 'sync'],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                print(f'[Remote Sync] Command completed with return code: {result.returncode}')
                if result.stdout:
                    print(f'[Remote Sync] Output: {result.stdout}')
                if result.stderr:
                    print(f'[Remote Sync] Errors: {result.stderr}')
            except subprocess.TimeoutExpired:
                print('[Remote Sync] Command timed out after 5 minutes')
            except Exception as e:
                print(f'[Remote Sync] Error executing command: {e}')
        
        # Start the command in a background thread
        thread = threading.Thread(target=run_gtasks_remote_sync, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Remote sync command started in background'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting remote sync: {str(e)}'
        }), 500


@api.route('/remote/tasks', methods=['GET'])
def api_remote_load_tasks():
    """
    Load tasks from remote database when local DB is missing.
    
    Query parameters:
        db_id: Optional specific database ID
        
    Response:
        {
            "success": True,
            "data": {
                "tasks": [...],
                "source": "remote_db_name",
                "loaded_from": "remote"
            }
        }
    """
    from services.remote_sync_service import RemoteSyncService
    from models.task import Task
    
    try:
        db_id = request.args.get('db_id')
        
        if db_id:
            tasks = RemoteSyncService.load_tasks_from_remote(db_id)
        else:
            tasks = RemoteSyncService.load_tasks_from_any_remote()
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': [t.to_dict() if hasattr(t, 'to_dict') else t for t in tasks],
                'source': 'remote',
                'loaded_from': 'remote'
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading tasks from remote: {str(e)}'
        }), 500
