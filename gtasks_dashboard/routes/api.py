"""
API Routes
"""
from flask import Blueprint, jsonify, request, Response
from typing import Optional
from services.data_manager import DataManager
import os
import sys
from pathlib import Path
import threading
import traceback

# Ensure gtasks_cli package is importable
_cli_src_path = Path(__file__).resolve().parent.parent.parent / 'gtasks_cli' / 'src'
if str(_cli_src_path) not in sys.path:
    sys.path.insert(0, str(_cli_src_path))

api = Blueprint('api', __name__)
data_manager = DataManager()

# In-memory state
_dashboard_state = {
    'tasks': {},
    'accounts': [],
    'current_account': None,
    'stats': {}
}

# Cache tracking for database file modification times
_last_db_mtimes = {}

# Background sync lock to prevent concurrent Google sync
_sync_lock = threading.Lock()


def _resolve_cli_account(account_id: Optional[str] = None) -> Optional[str]:
    """
    Resolve account_id to the appropriate account_name for gtasks_cli.
    If account_id corresponds to a real subdirectory under ~/.gtasks containing tasks.db,
    return that account_id.
    Otherwise, if account_id is None, 'demo', or 'default', or no account subdirectory exists,
    return None so gtasks_cli uses the root ~/.gtasks directory.
    """
    if not account_id or account_id in ('demo', 'default'):
        return None
    from pathlib import Path
    acc_dir = Path.home() / '.gtasks' / account_id
    if acc_dir.is_dir() and (acc_dir / 'tasks.db').exists():
        return account_id
    return None


def _sync_task_to_google_background(task_id: str, account_id: str):
    """Background task to sync task completion to Google Tasks (non-blocking)"""
    with _sync_lock:
        try:
            cli_account = _resolve_cli_account(account_id)
            print(f'[Background Sync] Starting sync for task {task_id} (account: {account_id} -> cli: {cli_account})')
            
            # Import here to avoid circular imports and only load when needed
            import sys
            import traceback
            from pathlib import Path
            from datetime import datetime
            
            # Add gtasks_cli to path
            gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
            if str(gtasks_cli_path) not in sys.path:
                sys.path.insert(0, str(gtasks_cli_path))
            
            from gtasks_cli.core.task_manager import TaskManager
            from gtasks_cli.storage.sqlite_storage import SQLiteStorage
            from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
            from gtasks_cli.models.task import TaskStatus, Task
            
            # Initialize components with resolved account
            storage = SQLiteStorage(account_name=cli_account)
            google_client = GoogleTasksClient(account_name=cli_account)
            
            # Connect to Google Tasks (non-blocking, uses cached credentials)
            if not google_client.connect(interactive=False):
                print(f'[Background Sync] Failed to connect to Google Tasks - credentials may need refresh')
                return
            
            # Get the task from local storage (or fallback to root storage if needed)
            task_dicts = storage.load_tasks()
            task = next((t for t in task_dicts if t.get('id') == task_id), None)
            
            if not task and cli_account is not None:
                root_storage = SQLiteStorage(account_name=None)
                task_dicts = root_storage.load_tasks()
                task = next((t for t in task_dicts if t.get('id') == task_id), None)
            
            # Fallback to _dashboard_state memory cache if task still not in storage
            if not task:
                for acc_tasks in _dashboard_state.get('tasks', {}).values():
                    found = next((t for t in acc_tasks if t.get('id') == task_id), None)
                    if found:
                        task = found
                        break
            
            if not task:
                print(f'[Background Sync] Task {task_id} not found in local storage or memory')
                return
            
            # Create Task object
            task_obj = Task(**task)
            
            # Update status to completed
            task_obj.status = TaskStatus.COMPLETED
            now = datetime.now()
            task_obj.completed_at = now
            task_obj.modified_at = now
            
            # Try to update via Google Tasks API
            try:
                tasklist_id = getattr(task_obj, 'tasklist_id', None) or task.get('tasklist_id') or '@default'
                updated = google_client.update_task(task_obj, tasklist_id)
                if updated:
                    print(f'[Background Sync] ✅ Successfully synced task {task_id} to Google Tasks')
                else:
                    print(f'[Background Sync] ⚠️ Google Tasks API returned empty response for {task_id}')
            except Exception as e:
                error_msg = str(e)
                if 'invalid_grant' in error_msg.lower() or 'credentials' in error_msg.lower():
                    print(f'[Background Sync] 🔑 Google credentials need refresh - sync pending')
                else:
                    print(f'[Background Sync] ❌ Error syncing to Google: {e}')
                    
        except Exception as e:
            print(f'[Background Sync] ❌ Unexpected error: {e}')
            import traceback
            traceback.print_exc()


def _sync_task_to_turso_background(task_id: str, account_id: str):
    """Background task to sync task completion to Turso Remote DB (non-blocking)"""
    try:
        cli_account = _resolve_cli_account(account_id)
        print(f'[Turso Background Sync] Starting sync for task {task_id} (account: {account_id} -> cli: {cli_account})')
        
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
        storage = SQLiteStorage(account_name=cli_account)
        task_dicts = storage.load_tasks()
        task = next((t for t in task_dicts if t.get('id') == task_id), None)
        
        if not task and cli_account is not None:
            root_storage = SQLiteStorage(account_name=None)
            task_dicts = root_storage.load_tasks()
            task = next((t for t in task_dicts if t.get('id') == task_id), None)
        
        if not task:
            for acc_tasks in _dashboard_state.get('tasks', {}).values():
                found = next((t for t in acc_tasks if t.get('id') == task_id), None)
                if found:
                    task = found
                    break
        
        if not task:
            print(f'[Turso Background Sync] Task {task_id} not found in local storage')
            return
        
        # Get active remote databases
        config_storage = SyncConfigStorage(account_name=cli_account)
        active_dbs = config_storage.get_active_remote_dbs()
        
        if not active_dbs:
            print(f'[Turso Background Sync] No active remote databases configured')
            return
        
        # Push the task to each active remote DB
        for db_config in active_dbs:
            try:
                remote_storage = LibSQLStorage(url=db_config.url, account_name=cli_account)
                # Get existing remote tasks
                remote_tasks = remote_storage.load_tasks()
                
                # Update or add the task
                updated_remote_tasks = []
                task_updated = False
                for rt in remote_tasks:
                    if rt.get('id') == task_id:
                        # Update existing task with completed status
                        rt['status'] = task['status']
                        rt['completed_at'] = task.get('completed_at')
                        rt['modified_at'] = task.get('modified_at', task.get('completed_at'))
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


def _get_account_db_path(account_id: Optional[str] = None) -> Optional[Path]:
    """Get the path to the sqlite database for the given account"""
    gtasks_path = data_manager.gtasks_path or (Path.home() / '.gtasks')
    if account_id and account_id not in ('demo', 'default'):
        acc_db = gtasks_path / account_id / 'tasks.db'
        if acc_db.exists():
            return acc_db
    root_db = gtasks_path / 'tasks.db'
    if root_db.exists():
        return root_db
    return None


def ensure_cache_fresh(account_id: Optional[str] = None):
    """Ensure in-memory task cache is up to date with the sqlite database file."""
    if not account_id:
        account_id = _dashboard_state.get('current_account')
    
    # Check CLI current account file for switches
    try:
        current_account_file = Path.home() / '.gtasks' / '.current_account'
        if current_account_file.exists():
            cli_acc = current_account_file.read_text().strip()
            if cli_acc and cli_acc != _dashboard_state.get('current_account'):
                if any(a.id == cli_acc for a in _dashboard_state.get('accounts', [])):
                    _dashboard_state['current_account'] = cli_acc
                    if not account_id:
                        account_id = cli_acc
    except Exception:
        pass

    db_path = _get_account_db_path(account_id)
    if not db_path or not db_path.exists():
        return

    try:
        current_mtime = os.path.getmtime(db_path)
        cache_key = account_id or '__default__'
        last_mtime = _last_db_mtimes.get(cache_key, 0)

        if current_mtime > last_mtime or account_id not in _dashboard_state['tasks']:
            print(f'[Cache] Database modified for account {account_id} (mtime {current_mtime} > {last_mtime}), reloading tasks...')
            tasks = data_manager.load_tasks_for_account(account_id)
            _dashboard_state['tasks'][account_id] = [t.to_dict() for t in tasks]
            _last_db_mtimes[cache_key] = current_mtime
    except Exception as e:
        print(f'[Cache] Error checking db mtime: {e}')


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
        db_path = _get_account_db_path(account.id)
        if db_path and db_path.exists():
            _last_db_mtimes[account.id or '__default__'] = os.path.getmtime(db_path)
    
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
    ensure_cache_fresh(current)
    current = _dashboard_state.get('current_account')
    if current:
        return _dashboard_state['tasks'].get(current, [])
    return []


@api.route('/data')
def api_data():
    """Get all dashboard data"""
    current_account_id = _dashboard_state.get('current_account')
    ensure_cache_fresh(current_account_id)
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
            cli_account = _resolve_cli_account(current_account_id)
            google_client = GoogleTasksClient(account_name=cli_account)
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
    account_id = request.args.get('account_id')
    if account_id:
        ensure_cache_fresh(account_id)
        tasks = _dashboard_state['tasks'].get(account_id, [])
    else:
        tasks = get_current_tasks()
    
    # Apply filters
    status = request.args.get('status')
    priority = request.args.get('priority')
    search = request.args.get('search')
    
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
            deleted_file = Path.home() / '.gtasks' / '.deleted_accounts'
            if deleted_file.exists():
                try:
                    deleted_set = set(line.strip().lower() for line in deleted_file.read_text().splitlines() if line.strip())
                    new_acc_id = (account_name or 'personal').lower().replace(' ', '_')
                    deleted_set.discard(new_acc_id)
                    deleted_file.write_text('\n'.join(deleted_set))
                except Exception:
                    pass

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


@api.route('/accounts/<account_id>', methods=['DELETE'])
def api_delete_account(account_id):
    """Delete an account and its associated tasks/credentials with soft/hard option"""
    import shutil
    import sqlite3
    import time
    from pathlib import Path

    if not account_id:
        return jsonify({'success': False, 'error': 'account_id required'}), 400

    is_hard = request.args.get('hard', 'true').lower() in ('true', '1')

    try:
        if is_hard:
            deleted_file = Path.home() / '.gtasks' / '.deleted_accounts'
            deleted_set = set()
            if deleted_file.exists():
                try:
                    deleted_set = set(line.strip().lower() for line in deleted_file.read_text().splitlines() if line.strip())
                except Exception:
                    pass
            deleted_set.add(account_id.lower())
            if account_id.lower() in ('default', 'personal'):
                deleted_set.add('default')
                deleted_set.add('personal')
            deleted_file.write_text('\n'.join(deleted_set))

            if account_id in ('default', 'personal'):
                db_path = Path.home() / '.gtasks' / 'tasks.db'
                if db_path.exists():
                    backup_path = Path.home() / '.gtasks' / f'tasks_backup_{int(time.time())}.db'
                    try:
                        shutil.copy2(db_path, backup_path)
                    except Exception:
                        pass
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM tasks")
                    conn.commit()
                    conn.close()
            else:
                acc_dir = Path.home() / '.gtasks' / account_id
                if acc_dir.exists() and acc_dir.is_dir():
                    shutil.rmtree(acc_dir)

        if account_id in _dashboard_state.get('tasks', {}):
            del _dashboard_state['tasks'][account_id]

        _dashboard_state['accounts'] = [a for a in _dashboard_state.get('accounts', []) if a.id != account_id]

        if _dashboard_state.get('current_account') == account_id:
            _dashboard_state['current_account'] = _dashboard_state['accounts'][0].id if _dashboard_state.get('accounts') else None
            try:
                (Path.home() / '.gtasks' / '.current_account').write_text(_dashboard_state['current_account'] or '')
            except Exception:
                pass

        refresh_dashboard_cache()
        return jsonify({
            'success': True,
            'message': f'Account {account_id} {"hard deleted" if is_hard else "soft deleted"} successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/accounts/<account_id>/restore', methods=['POST'])
def api_restore_account(account_id):
    """Restore an account from deleted status and restore tasks if backed up"""
    import shutil
    import sqlite3
    import time
    from pathlib import Path

    try:
        deleted_file = Path.home() / '.gtasks' / '.deleted_accounts'
        if deleted_file.exists():
            try:
                deleted_set = set(line.strip().lower() for line in deleted_file.read_text().splitlines() if line.strip())
                deleted_set.discard(account_id.lower())
                if account_id.lower() in ('default', 'personal'):
                    deleted_set.discard('default')
                    deleted_set.discard('personal')
                deleted_file.write_text('\n'.join(deleted_set))
            except Exception:
                pass

        if account_id.lower() in ('default', 'personal'):
            db_path = Path.home() / '.gtasks' / 'tasks.db'
            needs_restore = True
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    count = conn.cursor().execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
                    conn.close()
                    if count > 0:
                        needs_restore = False
                except Exception:
                    pass

            if needs_restore:
                backups = sorted((Path.home() / '.gtasks').glob('tasks_backup_*.db'), key=lambda p: p.stat().st_mtime, reverse=True)
                if backups:
                    shutil.copy2(backups[0], db_path)

        refresh_dashboard_cache()
        return jsonify({
            'success': True,
            'message': f'Account {account_id} restored successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@api.route('/auth/google/start', methods=['GET', 'POST'])
def api_auth_google_start():
    """
    Generate Google OAuth authorization URL for adding or connecting an account.
    Returns the auth URL so the app can launch the browser, or redirects directly.
    """
    from pathlib import Path
    import urllib.parse
    import json
    
    data = request.get_json(silent=True) or {}
    account_name = request.args.get('account_name') or data.get('account_name') or 'Personal'
    
    # Dynamically resolve redirect_uri from incoming Host header if not specified or set to auto
    redirect_uri = request.args.get('redirect_uri') or data.get('redirect_uri')
    if not redirect_uri or redirect_uri in ('auto', 'default'):
        # Dynamically build using current server host (supports localhost, LAN IP, or public domain HTTPS)
        base_host = request.host_url.rstrip('/')
        redirect_uri = f"{base_host}/api/auth/google/callback"

    # Master credentials file
    cred_file = Path.home() / '.gtasks' / 'credentials.json'
    if not cred_file.exists():
        return jsonify({
            'success': False,
            'error': 'Google OAuth credentials.json not found on server.'
        }), 404

    try:
        with open(cred_file, 'r') as f:
            cred_data = json.load(f)
        client_info = cred_data.get('installed') or cred_data.get('web') or {}
        client_id = client_info.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'Invalid credentials.json: client_id missing'}), 400

        scopes = [
            'https://www.googleapis.com/auth/tasks',
            'https://www.googleapis.com/auth/tasks.readonly',
            'openid',
            'email',
            'profile'
        ]

        # Use Google's standard OAuth2 auth endpoint
        auth_params = {
            'client_id': client_id,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob' if redirect_uri == 'oob' else redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(scopes),
            'access_type': 'offline',
            'prompt': 'consent',
            'state': account_name
        }

        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(auth_params)}"

        return jsonify({
            'success': True,
            'auth_url': auth_url,
            'account_name': account_name,
            'redirect_uri': redirect_uri,
            'client_id': client_id
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/auth/google/callback', methods=['GET', 'POST'])
def api_auth_google_callback():
    """
    Callback endpoint that Google redirects to after user approves permissions.
    Exchanges code for tokens and renders a user-friendly completion page.
    """
    from flask import Response
    import requests
    from pathlib import Path
    import json
    import sqlite3

    code = request.args.get('code')
    account_name = request.args.get('state') or 'Personal'
    error = request.args.get('error')

    if error:
        return Response(f"""<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Auth Cancelled</title></head>
<body style="font-family:sans-serif;text-align:center;padding:40px;background:#1e1e2e;color:#fff;">
  <h2 style="color:#ef4444;">Authorization Cancelled</h2>
  <p>{error}</p>
  <p><a href="/" style="color:#3b82f6;">Return to Dashboard</a></p>
</body>
</html>""", mimetype='text/html')

    if not code:
        return Response("Missing authorization code from Google.", status=400)

    # Reconstruct dynamic redirect_uri matching what was sent
    base_host = request.host_url.rstrip('/')
    redirect_uri = f"{base_host}/api/auth/google/callback"

    cred_file = Path.home() / '.gtasks' / 'credentials.json'
    if not cred_file.exists():
        return Response("Server credentials.json not found", status=500)

    try:
        with open(cred_file, 'r') as f:
            cred_data = json.load(f)
        client_info = cred_data.get('installed') or cred_data.get('web') or {}
        client_id = client_info.get('client_id')
        client_secret = client_info.get('client_secret')

        # Exchange code for tokens
        token_res = requests.post('https://oauth2.googleapis.com/token', data={
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        })

        token_json = token_res.json()
        if 'error' in token_json:
            return Response(f"Token exchange error: {token_json.get('error_description', token_json['error'])}", status=400)

        # Create account folder
        account_id = account_name.lower().replace(' ', '_')
        acc_dir = Path.home() / '.gtasks' / (account_id if account_id != 'default' else '')
        acc_dir.mkdir(parents=True, exist_ok=True)

        # Save token.json
        token_save_path = acc_dir / 'token.json'
        token_data_to_save = {
            'token': token_json.get('access_token'),
            'refresh_token': token_json.get('refresh_token'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': client_id,
            'client_secret': client_secret,
            'scopes': ['https://www.googleapis.com/auth/tasks']
        }
        with open(token_save_path, 'w') as f:
            json.dump(token_data_to_save, f, indent=2)

        # Copy credentials.json
        with open(acc_dir / 'credentials.json', 'w') as f:
            json.dump(cred_data, f, indent=2)

        # Initialize SQLite database
        db_path = acc_dir / 'tasks.db'
        if not db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    notes TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    due TEXT,
                    tags TEXT,
                    created_at TEXT,
                    modified_at TEXT,
                    completed_at TEXT,
                    list_title TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_lists (
                    task_id TEXT,
                    list_name TEXT,
                    PRIMARY KEY (task_id, list_name)
                )
            ''')
            conn.commit()
            conn.close()

        # Refresh cache and trigger initial sync
        refresh_dashboard_cache()
        threading.Thread(target=lambda: _sync_initial_pull(account_id), daemon=True).start()

        # Render clean mobile-friendly success landing page
        return Response(f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GTasks - Account Connected</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #0f172a;
      color: #f8fafc;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      padding: 20px;
      box-sizing: border-box;
    }}
    .card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 32px;
      max-width: 440px;
      text-align: center;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    .icon {{
      font-size: 54px;
      color: #10b981;
      margin-bottom: 16px;
    }}
    h2 {{ margin: 0 0 12px; font-size: 24px; font-weight: 700; }}
    p {{ color: #94a3b8; line-height: 1.5; margin: 0 0 24px; }}
    .btn {{
      display: inline-block;
      background: #3b82f6;
      color: #fff;
      text-decoration: none;
      padding: 12px 24px;
      border-radius: 10px;
      font-weight: 600;
      transition: background 0.2s;
    }}
    .btn:hover {{ background: #2563eb; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✓</div>
    <h2>Account Connected!</h2>
    <p>Google Tasks account <strong>{account_name}</strong> was linked successfully to the server. You can now close this tab and return to the GTasks app.</p>
    <a href="/" class="btn">Open Web Dashboard</a>
  </div>
</body>
</html>""", mimetype='text/html')

    except Exception as e:
        return Response(f"Internal error completing OAuth: {str(e)}", status=500)


@api.route('/auth/tokens/import', methods=['POST'])
def api_auth_tokens_import():
    """
    Directly import token credentials JSON from client to remote server.
    Allows zero-browser API provisioning.
    """
    from pathlib import Path
    import json
    import sqlite3

    data = request.get_json() or {}
    account_name = data.get('account_name', 'Personal').strip()
    token_data = data.get('token_data')

    if not token_data or not isinstance(token_data, dict):
        return jsonify({'success': False, 'error': 'token_data JSON object is required'}), 400

    account_id = account_name.lower().replace(' ', '_')
    acc_dir = Path.home() / '.gtasks' / (account_id if account_id != 'default' else '')
    acc_dir.mkdir(parents=True, exist_ok=True)

    with open(acc_dir / 'token.json', 'w') as f:
        json.dump(token_data, f, indent=2)

    # Master credentials copy
    cred_file = Path.home() / '.gtasks' / 'credentials.json'
    if cred_file.exists():
        import shutil
        shutil.copy(cred_file, acc_dir / 'credentials.json')

    # Seed SQLite database
    db_path = acc_dir / 'tasks.db'
    if not db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT, notes TEXT, priority TEXT, status TEXT, due TEXT, tags TEXT, created_at TEXT, modified_at TEXT, completed_at TEXT, list_title TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS task_lists (task_id TEXT, list_name TEXT, PRIMARY KEY (task_id, list_name))''')
        conn.commit()
        conn.close()

    refresh_dashboard_cache()
    threading.Thread(target=lambda: _sync_initial_pull(account_id), daemon=True).start()

    return jsonify({'success': True, 'account_id': account_id, 'message': f"Tokens imported successfully for '{account_name}'"})


@api.route('/auth/google/submit-code', methods=['POST'])
def api_auth_google_submit_code():
    """
    Exchange an authorization code for tokens and provision the account.
    Supports in-app paste of code (oob) or direct redirect code submission.
    """
    import os
    import requests
    from pathlib import Path
    import json
    import sqlite3

    data = request.get_json() or {}
    code = data.get('code', '').strip()
    account_name = data.get('account_name', 'Personal').strip()
    
    # Auto-resolve redirect_uri matching incoming Host if not given
    redirect_uri = data.get('redirect_uri')
    if not redirect_uri or redirect_uri in ('auto', 'default'):
        base_host = request.host_url.rstrip('/')
        redirect_uri = f"{base_host}/api/auth/google/callback"

    if not code:
        return jsonify({'success': False, 'error': 'Authorization code is required'}), 400

    cred_file = Path.home() / '.gtasks' / 'credentials.json'
    if not cred_file.exists():
        return jsonify({'success': False, 'error': 'credentials.json not found'}), 404

    try:
        with open(cred_file, 'r') as f:
            cred_data = json.load(f)
        client_info = cred_data.get('installed') or cred_data.get('web') or {}
        client_id = client_info.get('client_id')
        client_secret = client_info.get('client_secret')

        # Exchange code for tokens with candidate redirect URIs
        candidate_uris = [
            'urn:ietf:wg:oauth:2.0:oob' if redirect_uri == 'oob' else redirect_uri,
            'http://localhost:48275',
            'http://127.0.0.1:48275',
            'http://localhost',
            f"{base_host}/api/auth/google/callback",
            'urn:ietf:wg:oauth:2.0:oob',
        ]

        token_json = {}
        for cand_uri in candidate_uris:
            token_res = requests.post('https://oauth2.googleapis.com/token', data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': cand_uri,
                'grant_type': 'authorization_code'
            })
            token_json = token_res.json()
            if 'error' not in token_json:
                break
            if token_json.get('error') != 'redirect_uri_mismatch':
                break

        if 'error' in token_json:
            return jsonify({'success': False, 'error': token_json.get('error_description', token_json['error'])}), 400

        # Create account folder
        account_id = account_name.lower().replace(' ', '_')
        deleted_file = Path.home() / '.gtasks' / '.deleted_accounts'
        if deleted_file.exists():
            try:
                deleted_set = set(line.strip().lower() for line in deleted_file.read_text().splitlines() if line.strip())
                deleted_set.discard(account_id.lower())
                deleted_file.write_text('\n'.join(deleted_set))
            except Exception:
                pass

        acc_dir = Path.home() / '.gtasks' / (account_id if account_id != 'default' else '')
        acc_dir.mkdir(parents=True, exist_ok=True)

        # Save token.json
        token_save_path = acc_dir / 'token.json'
        token_data_to_save = {
            'token': token_json.get('access_token'),
            'refresh_token': token_json.get('refresh_token'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': client_id,
            'client_secret': client_secret,
            'scopes': ['https://www.googleapis.com/auth/tasks']
        }
        with open(token_save_path, 'w') as f:
            json.dump(token_data_to_save, f, indent=2)

        # Copy credentials.json
        with open(acc_dir / 'credentials.json', 'w') as f:
            json.dump(cred_data, f, indent=2)

        # Initialize SQLite database if not present
        db_path = acc_dir / 'tasks.db'
        if not db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    notes TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    due TEXT,
                    tags TEXT,
                    created_at TEXT,
                    modified_at TEXT,
                    completed_at TEXT,
                    list_title TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_lists (
                    task_id TEXT,
                    list_name TEXT,
                    PRIMARY KEY (task_id, list_name)
                )
            ''')
            conn.commit()
            conn.close()

        # Refresh cache and trigger initial sync
        refresh_dashboard_cache()

        # Trigger background pull
        threading.Thread(target=lambda: _sync_initial_pull(account_id), daemon=True).start()

        return jsonify({
            'success': True,
            'account_id': account_id,
            'message': f"Account '{account_name}' connected and initialized successfully!"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def _sync_initial_pull(account_name: str):
    """Background helper to pull initial tasks for new account matching CLI advanced-sync"""
    try:
        import sys
        from pathlib import Path
        gtasks_cli_path = Path(__file__).parent.parent.parent / 'gtasks_cli' / 'src'
        if str(gtasks_cli_path) not in sys.path:
            sys.path.insert(0, str(gtasks_cli_path))
        from gtasks_cli.core.task_manager import TaskManager
        from gtasks_cli.integrations.advanced_sync_manager import AdvancedSyncManager

        cli_acc = None if account_name in ('default', 'personal') else account_name
        task_manager = TaskManager(use_google_tasks=True, storage_backend='sqlite', account_name=cli_acc)
        sync_manager = AdvancedSyncManager(task_manager.storage, task_manager.google_client)
        sync_manager.pull_from_google()
        refresh_dashboard_cache()
        print(f"[OAuth Onboarding] Initial task sync completed for {account_name}")
    except Exception as e:
        print(f"[OAuth Onboarding] Initial pull warning: {e}")


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
        'hybrid_tags': {
            'bracket': list(dict.fromkeys(extracted_tags)),
            'hash': [],
            'user': []
        },
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

        cli_account = _resolve_cli_account(account_id)
        google_client = GoogleTasksClient(account_name=cli_account)
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

            created_google_task = google_client.create_task(cli_task, existing_signatures=set())
            if created_google_task:
                synced_to_google = True
                print(f"[API] ✅ New task {task_id} synced immediately to Google Tasks list '{list_title}' (Google ID: {created_google_task.id})")
                if created_google_task.id and created_google_task.id != task_id:
                    new_gid = created_google_task.id
                    try:
                        import sqlite3
                        db_path = _get_account_db_path(account_id)
                        if db_path and db_path.exists():
                            with sqlite3.connect(db_path, timeout=10.0) as conn:
                                conn.execute("UPDATE tasks SET id = ? WHERE id = ?", (new_gid, task_id))
                                conn.execute("UPDATE task_lists SET task_id = ? WHERE task_id = ?", (new_gid, task_id))
                                conn.commit()
                        new_task['id'] = new_gid
                        task_id = new_gid
                    except Exception as id_err:
                        print(f"[API] Error updating local task ID to Google ID: {id_err}")
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
    if 'hybrid_tags' not in target_task or not isinstance(target_task['hybrid_tags'], dict):
        target_task['hybrid_tags'] = {'bracket': [], 'hash': [], 'user': []}
    target_task['hybrid_tags']['bracket'] = list(dict.fromkeys(extracted_tags))

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
        cli_account = _resolve_cli_account(target_account)
        google_client = GoogleTasksClient(account_name=cli_account)
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
# SETTINGS & CONFIGURATION ENDPOINTS
# ============================================

@api.route('/settings', methods=['GET'])
def api_get_settings():
    """Get merged configuration and feature flags"""
    try:
        from gtasks_cli.storage.config_manager import ConfigManager
        from config import FEATURE_FLAGS

        account = request.args.get('account') or _dashboard_state.get('current_account')
        cli_account = _resolve_cli_account(account)
        cm = ConfigManager(account_name=cli_account)

        # Clone config dict
        cfg = dict(cm.config)
        # Mask sensitive email password if present
        if 'email' in cfg and isinstance(cfg['email'], dict):
            email_cfg = dict(cfg['email'])
            if email_cfg.get('password'):
                email_cfg['password'] = '••••••••'
            cfg['email'] = email_cfg

        return jsonify({
            'success': True,
            'data': {
                'config': cfg,
                'feature_flags': FEATURE_FLAGS,
                'config_path': str(cm.config_path)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api.route('/settings', methods=['POST'])
def api_update_settings():
    """Update configuration settings in config.yaml"""
    try:
        from gtasks_cli.storage.config_manager import ConfigManager
        data = request.get_json() or {}
        account = data.get('account') or _dashboard_state.get('current_account')
        cli_account = _resolve_cli_account(account)
        cm = ConfigManager(account_name=cli_account)

        updates = data.get('settings', {})
        for key, val in updates.items():
            # If email.password is masked, skip updating it
            if key in ('email.password', 'password') and str(val).startswith('•••'):
                continue
            cm.set(key, val)

        # Update FEATURE_FLAGS in memory if provided
        feature_updates = data.get('feature_flags', {})
        if feature_updates:
            from config import FEATURE_FLAGS
            for fk, fv in feature_updates.items():
                if fk in FEATURE_FLAGS:
                    FEATURE_FLAGS[fk] = bool(fv)

        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'data': cm.config
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# ADVANCED DEBUGGER & LOGS ENDPOINTS
# ============================================

@api.route('/debug/diagnostics', methods=['GET'])
def api_debug_diagnostics():
    """Run comprehensive system diagnostics"""
    import os
    import sys
    import sqlite3
    import platform
    from pathlib import Path
    from gtasks_cli.utils.logger import get_log_file_path

    account = request.args.get('account') or _dashboard_state.get('current_account')
    cli_account = _resolve_cli_account(account)

    db_path = Path.home() / '.gtasks' / (f"{cli_account}/tasks.db" if cli_account else "tasks.db")
    log_path = get_log_file_path()

    db_info = {'exists': db_path.exists(), 'path': str(db_path), 'size_bytes': 0, 'tables': {}, 'healthy': False}
    if db_path.exists():
        try:
            db_info['size_bytes'] = db_path.stat().st_size
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cur.fetchall()]
            for tbl in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                    db_info['tables'][tbl] = cur.fetchone()[0]
                except Exception:
                    db_info['tables'][tbl] = 'error'
            
            # Quick integrity check
            cur.execute("PRAGMA quick_check;")
            check = cur.fetchone()
            db_info['healthy'] = (check and check[0] == 'ok')
            conn.close()
        except Exception as err:
            db_info['error'] = str(err)

    # Memory state summary
    accounts_loaded = list(_dashboard_state.get('tasks', {}).keys())
    tasks_count = sum(len(v) for v in _dashboard_state.get('tasks', {}).values())

    return jsonify({
        'success': True,
        'data': {
            'system': {
                'os': platform.system(),
                'platform': platform.platform(),
                'python_version': sys.version.split()[0],
                'pid': os.getpid()
            },
            'database': db_info,
            'log_file': {
                'path': str(log_path),
                'exists': log_path.exists(),
                'size_bytes': log_path.stat().st_size if log_path.exists() else 0
            },
            'dashboard_state': {
                'current_account': account,
                'resolved_cli_account': cli_account,
                'cached_accounts': accounts_loaded,
                'cached_tasks_total': tasks_count
            }
        }
    })


@api.route('/debug/logs', methods=['GET'])
def api_debug_logs():
    """Retrieve recent application logs with filtering"""
    from gtasks_cli.utils.logger import get_recent_logs, get_log_file_path
    limit = int(request.args.get('limit', 150))
    level = request.args.get('level')
    search = request.args.get('search')

    logs = get_recent_logs(lines=limit, level=level, search=search)
    log_file = get_log_file_path()

    return jsonify({
        'success': True,
        'data': {
            'logs': logs,
            'total_lines': len(logs),
            'file_size': log_file.stat().st_size if log_file.exists() else 0
        }
    })


@api.route('/debug/toggle', methods=['POST'])
def api_debug_toggle():
    """Dynamically set the logging level"""
    from gtasks_cli.utils.logger import set_global_log_level
    data = request.get_json() or {}
    level = data.get('level', 'DEBUG').upper()
    active_level = set_global_log_level(level)

    return jsonify({
        'success': True,
        'active_level': active_level,
        'message': f"Log level switched to {active_level}"
    })


@api.route('/debug/clear-logs', methods=['POST'])
def api_debug_clear_logs():
    """Clear application logs"""
    from gtasks_cli.utils.logger import clear_logs
    success = clear_logs()
    return jsonify({
        'success': success,
        'message': 'Logs cleared successfully' if success else 'Failed to clear logs'
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


@api.route('/tasks/<task_id>/delete', methods=['POST'])
def api_delete_task(task_id):
    """Delete a task from local SQLite and sync delete with Google Tasks"""
    from datetime import datetime
    import threading
    data = request.get_json() or {}
    account_id = data.get('account_id') or data.get('account') or _dashboard_state.get('current_account')
    permanent = data.get('permanent', False)
    
    try:
        # 1. Update/delete in SQLite
        db_path = data_manager.gtasks_path / account_id / 'tasks.db' if (account_id and data_manager.gtasks_path) else None
        if not db_path or not db_path.exists():
            db_path = data_manager.gtasks_path / 'tasks.db' if data_manager.gtasks_path else None

        if db_path and db_path.exists():
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            if permanent:
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                cursor.execute("DELETE FROM task_lists WHERE task_id = ?", (task_id,))
            else:
                cursor.execute("UPDATE tasks SET status = 'deleted', modified_at = ? WHERE id = ?", (datetime.now().isoformat(), task_id))
            conn.commit()
            conn.close()

        # 2. Update memory state
        for acc in _dashboard_state.get('tasks', {}):
            _dashboard_state['tasks'][acc] = [t for t in _dashboard_state['tasks'][acc] if t.get('id') != task_id]

        if permanent:
            data_manager.permanently_delete_task(task_id, account_id)
        else:
            data_manager.soft_delete_task(task_id, account_id)

        # 3. Background delete from Google Tasks
        def _delete_google():
            try:
                from gtasks_cli.integrations.google_tasks_client import GoogleTasksClient
                cli_account = _resolve_cli_account(account_id)
                google_client = GoogleTasksClient(account_name=cli_account)
                if google_client.connect(interactive=False):
                    google_client.delete_task(task_id)
            except Exception as ge:
                print(f"[Background Delete] Notice: {ge}")

        threading.Thread(target=_delete_google, daemon=True).start()

        return jsonify({
            'success': True,
            'message': 'Task deleted successfully'
        })
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
    data = request.get_json() or {}
    report_type = data.get('report_type')
    filters = data.get('filters', {})
    parameters = data.get('parameters', {})
    account_id = data.get('account') or filters.get('account') or _dashboard_state.get('current_account')
    
    if not report_type:
        return jsonify({
            'success': False,
            'message': 'Report type is required'
        }), 400
    
    try:
        # Load tasks for specific account or all accounts
        raw_tasks = []
        if account_id and account_id != 'all':
            raw_tasks = _dashboard_state['tasks'].get(account_id, [])
            if not raw_tasks:
                # Reload if memory was cold
                tasks_objs = data_manager.load_tasks_for_account(account_id)
                raw_tasks = [t.to_dict() for t in tasks_objs]
        else:
            for acc_tasks in _dashboard_state['tasks'].values():
                raw_tasks.extend(acc_tasks)

        # Apply basic filters (list, tags, status) if specified in parameters or filters
        list_filter = filters.get('list_id') or parameters.get('list_id')
        if list_filter and list_filter != 'all':
            raw_tasks = [t for t in raw_tasks if t.get('tasklist_id') == list_filter]

        tag_filter = filters.get('tags') or parameters.get('tags')
        if tag_filter:
            tags_to_match = [tag_filter] if isinstance(tag_filter, str) else tag_filter
            raw_tasks = [t for t in raw_tasks if any(tg in (t.get('tags') or []) for tg in tags_to_match)]

        # Generate report
        report_data = data_manager.generate_report(report_type, raw_tasks, **parameters)
        
        return jsonify({
            'success': True,
            'data': report_data,
            'message': f'Report {report_type} generated successfully'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error generating report: {str(e)}'
        }), 500


@api.route('/reports/export', methods=['POST'])
def api_export_report():
    """Export a generated report to csv, json, or txt"""
    data = request.get_json() or {}
    report_type = data.get('report_type')
    report_data = data.get('report_data', {})
    export_format = data.get('format', 'txt').lower()
    filename = data.get('filename') or f"{report_type}_report.{export_format}"

    if not report_type or not report_data:
        return jsonify({
            'success': False,
            'message': 'report_type and report_data are required'
        }), 400

    try:
        content = data_manager.export_report(report_type, report_data, format=export_format)
        
        mimetypes = {
            'csv': 'text/csv',
            'json': 'application/json',
            'txt': 'text/plain'
        }
        mimetype = mimetypes.get(export_format, 'text/plain')
        
        return Response(
            content,
            mimetype=mimetype,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error exporting report: {str(e)}'
        }), 500


@api.route('/reports/email', methods=['POST'])
def api_email_report():
    """Send a generated report via email"""
    data = request.get_json() or {}
    report_type = data.get('report_type')
    report_data = data.get('report_data', {})
    recipients = data.get('recipients', [])
    cc = data.get('cc', [])
    bcc = data.get('bcc', [])
    subject = data.get('subject')

    if not recipients:
        return jsonify({
            'success': False,
            'message': 'At least one recipient email is required'
        }), 400

    if not report_data:
        return jsonify({
            'success': False,
            'message': 'report_data is required'
        }), 400

    try:
        from gtasks_cli.utils.email_sender import EmailSender
        sender = EmailSender()

        # Format body content: prefer text export of the report
        body = data_manager.export_report(report_type or 'report', report_data, format='txt')

        if not subject:
            report_name = report_data.get('report_name') or report_data.get('title') or (report_type.upper() if report_type else 'Report')
            subject = f"GTasks Report: {report_name}"

        success = sender.send_email(
            to_emails=recipients,
            subject=subject,
            body=body,
            html=True,
            cc_emails=cc,
            bcc_emails=bcc
        )

        if success:
            return jsonify({
                'success': True,
                'message': f"Report successfully emailed to {', '.join(recipients if isinstance(recipients, list) else [recipients])}"
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send email. Please check SMTP configuration or credentials (GTASKS_EMAIL_USER / GTASKS_EMAIL_PASSWORD).'
            }), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error dispatching email: {str(e)}'
        }), 500


# ============================================
# NOTIFICATIONS ENDPOINTS
# ============================================

@api.route('/notifications', methods=['GET'])
def api_list_notifications():
    """List notifications with unread counts"""
    try:
        from gtasks_cli.notifications.manager import NotificationManager
        account = request.args.get('account') or _dashboard_state.get('current_account')
        cli_account = _resolve_cli_account(account)
        
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))

        nm = NotificationManager(account_name=cli_account)
        items = nm.list_notifications(unread_only=unread_only, limit=limit)
        unread_count = nm.get_unread_count()

        return jsonify({
            'success': True,
            'data': {
                'notifications': items,
                'unread_count': unread_count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api.route('/notifications/read', methods=['POST'])
def api_read_notifications():
    """Mark a notification or all notifications as read"""
    try:
        from gtasks_cli.notifications.manager import NotificationManager
        data = request.get_json() or {}
        notif_id = data.get('id')  # If None, marks all as read
        account = data.get('account') or _dashboard_state.get('current_account')
        cli_account = _resolve_cli_account(account)

        nm = NotificationManager(account_name=cli_account)
        success = nm.mark_as_read(notif_id=notif_id)

        return jsonify({
            'success': success,
            'message': 'Notifications marked as read' if success else 'Failed to mark as read',
            'unread_count': nm.get_unread_count()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api.route('/notifications/clear', methods=['POST'])
def api_clear_notifications():
    """Clear a single notification or all notifications"""
    try:
        from gtasks_cli.notifications.manager import NotificationManager
        data = request.get_json() or {}
        notif_id = data.get('id')
        account = data.get('account') or _dashboard_state.get('current_account')
        cli_account = _resolve_cli_account(account)

        nm = NotificationManager(account_name=cli_account)
        success = nm.clear(notif_id=notif_id)

        return jsonify({
            'success': success,
            'message': 'Notifications cleared' if success else 'Failed to clear notifications',
            'unread_count': nm.get_unread_count()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api.route('/notifications/check', methods=['POST'])
def api_check_notifications():
    """Scan tasks and generate alerts for overdue or upcoming deadlines"""
    try:
        from gtasks_cli.notifications.manager import NotificationManager
        data = request.get_json(silent=True) or {}
        account = data.get('account') or _dashboard_state.get('current_account')
        cli_account = _resolve_cli_account(account)

        tasks = []
        if cli_account and cli_account in _dashboard_state.get('tasks', {}):
            tasks = _dashboard_state['tasks'][cli_account]
        else:
            for acc_tasks in _dashboard_state.get('tasks', {}).values():
                tasks.extend(acc_tasks)

        if not tasks:
            tasks_objs = data_manager.load_tasks_for_account(account or 'default')
            tasks = [t.to_dict() for t in tasks_objs]

        nm = NotificationManager(account_name=cli_account)
        new_alerts = nm.evaluate_task_alerts(tasks)

        return jsonify({
            'success': True,
            'data': {
                'new_alerts': new_alerts,
                'unread_count': nm.get_unread_count()
            },
            'message': f"Scan completed. Generated {len(new_alerts)} alert(s)."
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


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
    account_id = data.get('account_id') or data.get('account') or _dashboard_state.get('current_account')
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
                        if db_path.exists():
                            _last_db_mtimes[acc_id or '__default__'] = os.path.getmtime(db_path)
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
        sync_all = bool(data.get('sync_all', False) or data.get('all', False))
        account = data.get('account')
        
        if not account:
            account = _dashboard_state.get('current_account')

        # Validate sync_type
        if sync_type not in ('push', 'pull', 'both'):
            return jsonify({
                'success': False,
                'message': 'Invalid sync_type. Must be "push", "pull", or "both"'
            }), 400
        
        # Start the sync (with sync_all support matching 'gtasks advanced-sync --all')
        sync_id = SyncService.start_advanced_sync(sync_type=sync_type, account=account, sync_all=sync_all)
        
        return jsonify({
            'success': True,
            'sync_id': sync_id,
            'sync_all': sync_all,
            'message': f'Started {"full " if sync_all else ""}{sync_type} sync'
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


@api.route('/ai/ask', methods=['POST'])
def api_ai_ask():
    """Execute a single-shot natural language query via AIClient"""
    try:
        data = request.get_json() or {}
        query = data.get('query') or data.get('message') or ''
        account = data.get('account')
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
            
        cli_account = _resolve_cli_account(account)
        from gtasks_cli.core.task_manager import TaskManager
        from gtasks_cli.ai.client import AIClient
        
        tm = TaskManager(storage_backend='sqlite', account_name=cli_account)
        ai_client = AIClient(tm, account_name=cli_account)
        
        reply = ai_client.ask(query)
        return jsonify({
            'success': True,
            'reply': reply,
            'result': reply
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/ai/chat', methods=['POST'])
def api_ai_chat():
    """Process a turn in conversational chat via AIClient"""
    try:
        data = request.get_json() or {}
        message = data.get('message') or data.get('query') or ''
        account = data.get('account')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
            
        cli_account = _resolve_cli_account(account)
        from gtasks_cli.core.task_manager import TaskManager
        from gtasks_cli.ai.client import AIClient
        
        tm = TaskManager(storage_backend='sqlite', account_name=cli_account)
        ai_client = AIClient(tm, account_name=cli_account)
        
        reply = ai_client.chat_turn(message)
        return jsonify({
            'success': True,
            'reply': reply
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/openapi.json', methods=['GET'])
def get_openapi_spec():
    """Serve the OpenAPI 3.0 specification JSON"""
    import os
    spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'openapi.json')
    if os.path.exists(spec_path):
        with open(spec_path, 'r') as f:
            return Response(f.read(), mimetype='application/json')
    return jsonify({'error': 'OpenAPI spec not found'}), 404


@api.route('/docs', methods=['GET'])
def swagger_ui():
    """Interactive Swagger UI Documentation"""
    swagger_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GTasks API Documentation (Swagger UI)</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
    <link rel="icon" type="image/png" href="https://unpkg.com/swagger-ui-dist@5.11.0/favicon-32x32.png" sizes="32x32" />
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin:0; background: #fafafa; }
        .topbar { display: none; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"></script>
    <script>
    window.onload = function() {
        window.ui = SwaggerUIBundle({
            url: "/api/openapi.json",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            layout: "StandaloneLayout"
        });
    };
    </script>
</body>
</html>"""
    return Response(swagger_html, mimetype='text/html')
