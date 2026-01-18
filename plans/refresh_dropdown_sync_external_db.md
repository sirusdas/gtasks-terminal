# Refresh Dropdown Enhancement - Implementation Plan

## Overview
Add "Sync External DB" option to the dashboard header's refresh dropdown that runs `gtasks remote sync` command in a background thread.

## Files to Modify

### 1. `gtasks_dashboard/templates/dashboard.html`
**Location:** Lines 70-77 (refresh dropdown menu)

**Change:** Add new menu item for "Sync External DB"

```html
<div class="refresh-dropdown-menu" id="refresh-dropdown-menu">
    <a href="#" onclick="refreshData(); toggleRefreshDropdown(); return false;">
        <i class="fas fa-database"></i> Refresh Cache
    </a>
    <a href="#" onclick="syncAndRefresh(); toggleRefreshDropdown(); return false;">
        <i class="fas fa-sync"></i> Sync Data
    </a>
    <a href="#" onclick="syncRemoteDb(); toggleRefreshDropdown(); return false;">
        <i class="fas fa-cloud-upload-alt"></i> Sync External DB  <!-- NEW -->
    </a>
</div>
```

### 2. `gtasks_dashboard/routes/api.py`
**Location:** Add new endpoint after existing remote sync endpoints (around line 228)

**New endpoint:**
```python
@app.route('/api/remote/sync-command', methods=['POST'])
def api_remote_sync_command():
    """Execute gtasks remote sync command in background thread."""
    from services.remote_sync_service import RemoteSyncService
    return RemoteSyncService.execute_remote_sync_command()
```

### 3. `gtasks_dashboard/services/remote_sync_service.py`
**Location:** Add new class method (around line 330)

**New method:**
```python
@classmethod
def execute_remote_sync_command(cls) -> Dict[str, Any]:
    """Execute gtasks remote sync command in a background thread."""
    import subprocess
    import threading
    
    try:
        # Start the command in a background thread
        def run_command():
            subprocess.run(
                ['gtasks', 'remote', 'sync'],
                capture_output=True,
                text=True
            )
        
        thread = threading.Thread(target=run_command, daemon=True)
        thread.start()
        
        return {
            'success': True,
            'message': 'Remote sync command started in background'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

### 4. `gtasks_dashboard/static/js/dashboard.js`
**Location:** Add new function around line 505

**New function:**
```javascript
/**
 * Execute remote sync command
 * This runs gtasks remote sync in background and refreshes dashboard on completion
 */
export async function syncRemoteDb() {
    console.log('[Dashboard] Executing remote sync command...');
    showNotification('Starting remote sync... ⏳', 'info');
    
    try {
        const response = await fetch(apiEndpoints.remote.syncCommand, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('[Dashboard] Remote sync command started');
            
            // Wait a moment then refresh dashboard to show updated data
            setTimeout(async () => {
                await loadDashboard();
                showNotification('Remote sync completed! ✅', 'success');
            }, 3000);
        } else {
            showNotification(data.error || 'Failed to start remote sync', 'error');
        }
    } catch (error) {
        console.error('[Dashboard] Error executing remote sync:', error);
        showNotification('Error executing remote sync', 'error');
    }
}
```

**Location:** Update `window` exports (around line 1555)
```javascript
window.syncRemoteDb = syncRemoteDb;
```

### 5. `gtasks_dashboard/static/js/constants.js`
**Location:** Add new endpoint to apiEndpoints object

```javascript
remote: {
    // ... existing endpoints ...
    syncCommand: `${BASE_PATH}/api/remote/sync-command`  // NEW
}
```

## Execution Flow

```
User clicks "Sync External DB"
        │
        ▼
JavaScript: syncRemoteDb()
        │
        ▼
API: POST /api/remote/sync-command
        │
        ▼
Python: RemoteSyncService.execute_remote_sync_command()
        │
        ▼
Thread: subprocess.run(['gtasks', 'remote', 'sync'])
        │
        ▼
3 second delay → loadDashboard() → showNotification()
```

## Testing Checklist

- [ ] Click "Sync External DB" and verify command executes
- [ ] Verify dashboard refreshes after sync completes
- [ ] Verify notification messages display correctly
- [ ] Verify no UI blocking during sync
- [ ] Verify dropdown closes after selection

## Estimated Effort

- HTML changes: 2 minutes
- API endpoint: 5 minutes
- Python threading logic: 5 minutes
- JavaScript function: 5 minutes
- Testing: 5 minutes

**Total: ~22 minutes**
