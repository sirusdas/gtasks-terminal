# Mark Complete Feature Implementation Plan

## Overview
Add a checkbox/tick icon next to each task in both the Hierarchy menu (task panel) and Tasks menu that allows users to mark tasks as complete with immediate sync to Google Tasks.

## Architecture

```mermaid
graph TD
    A[User clicks checkbox] --> B[Call API /api/tasks/{id}/complete]
    B --> C[DataManager.complete_task]
    C --> D[Update local SQLite]
    C --> E[Sync to Google Tasks API]
    E --> F[Return success]
    D --> F
    F --> G[Update UI - show completed state]
```

## Implementation Steps

### 1. Backend API - Add Complete Task Endpoint

**File:** `gtasks_dashboard/routes/api.py`

Add new endpoint:
```python
@api.route('/api/tasks/<task_id>/complete', methods=['POST'])
def api_complete_task(task_id):
    """Mark a task as completed"""
    data = request.get_json() or {}
    account_id = data.get('account_id', _dashboard_state.get('current_account'))
    
    try:
        success = data_manager.complete_task(task_id, account_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Task completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error completing task: {str(e)}'
        }), 500
```

### 2. Data Manager - Add Complete Task Method

**File:** `gtasks_dashboard/services/data_manager.py`

Add method to `DataManager` class:
```python
def complete_task(self, task_id: str, account_id: Optional[str] = None) -> bool:
    """Complete a task and sync to Google Tasks"""
    current_account = account_id or self.dashboard_state['current_account']
    
    if current_account in self.dashboard_state['tasks']:
        for task in self.dashboard_state['tasks'][current_account]:
            if task.id == task_id:
                task.status = 'completed'
                task.completed_at = datetime.now().isoformat()
                
                # Sync to Google Tasks
                self._sync_task_to_google(task, current_account)
                return True
    return False

def _sync_task_to_google(self, task: Task, account_id: str):
    """Sync task completion to Google Tasks API"""
    # Implementation to call gtasks CLI or Google Tasks API
    # This will use the existing sync infrastructure
    pass
```

### 3. Dashboard JavaScript - Add Complete Task Function

**File:** `gtasks_dashboard/static/js/dashboard.js`

Add function to handle task completion:
```javascript
/**
 * Mark a task as complete
 * @param {string} taskId - The task ID to complete
 * @param {string} accountId - Optional account ID
 */
async function completeTask(taskId, accountId = null) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                account_id: accountId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Task completed:', taskId);
            
            // Update UI - change task appearance to completed
            updateTaskCompletedState(taskId);
            
            // Show success feedback
            showNotification('Task marked as complete', 'success');
            
            // Refresh data to update stats
            refreshData();
        } else {
            showNotification(data.message || 'Failed to complete task', 'error');
        }
    } catch (error) {
        console.error('Error completing task:', error);
        showNotification('Error completing task', 'error');
    }
}

/**
 * Update task UI to show completed state
 * @param {string} taskId - The task ID that was completed
 */
function updateTaskCompletedState(taskId) {
    // Update in tasks grid
    const taskElement = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
    if (taskElement) {
        taskElement.classList.add('completed');
        taskElement.querySelector('.task-complete-btn').innerHTML = '✅';
        taskElement.querySelector('.task-complete-btn').title = 'Completed';
    }
    
    // Update in hierarchy task panel
    const nodeTaskElement = document.querySelector(`.node-task-item[data-task-id="${taskId}"]`);
    if (nodeTaskElement) {
        nodeTaskElement.classList.add('completed');
        nodeTaskElement.querySelector('.task-complete-btn').innerHTML = '✅';
    }
}
```

### 4. Update Task Rendering - Add Checkbox

**File:** `gtasks_dashboard/static/js/dashboard.js`

Modify `renderTasks` function to include complete checkbox:
```javascript
function renderTasks(tasks) {
    const grid = document.getElementById('tasks-grid');
    if (!grid) return;
    
    grid.innerHTML = tasks.map(task => `
        <div class="task-item ${task.status === 'completed' ? 'completed' : ''}" data-task-id="${task.id}">
            <div class="task-complete-btn" onclick="completeTask('${task.id}')" 
                 title="${task.status === 'completed' ? 'Completed' : 'Mark as complete'}">
                ${task.status === 'completed' ? '✅' : '⭕'}
            </div>
            <div class="task-content">
                <div class="task-title">${escapeHtml(task.title)}</div>
                <div class="task-meta">
                    <span class="priority-badge ${task.calculated_priority}">${task.calculated_priority}</span>
                    <span class="due-date">Due: ${task.due || 'No date'}</span>
                </div>
            </div>
        </div>
    `).join('');
}
```

### 5. Hierarchy Task Panel - Add Checkbox

**File:** `gtasks_dashboard/static/js/hierarchy-task-panel.js`

Modify task rendering to include complete checkbox:
```javascript
function displayNodeTasks(tasks) {
    const grid = document.getElementById('node-tasks-grid');
    if (!grid) return;
    
    grid.innerHTML = tasks.map(task => `
        <div class="node-task-item ${task.status === 'completed' ? 'completed' : ''}" data-task-id="${task.id}">
            <div class="task-complete-btn" onclick="completeTask('${task.id}')"
                 title="${task.status === 'completed' ? 'Completed' : 'Mark as complete'}">
                ${task.status === 'completed' ? '✅' : '⭕'}
            </div>
            <div class="task-details">
                <div class="task-title">${escapeHtml(task.title)}</div>
                <div class="task-info">
                    <span class="priority-badge ${task.calculated_priority}">${task.calculated_priority}</span>
                    <span class="status-badge ${task.status}">${task.status}</span>
                    <span class="due-date">${task.due || 'No due date'}</span>
                </div>
            </div>
        </div>
    `).join('');
}
```

### 6. Add CSS Styles

**File:** `gtasks_dashboard/static/css/components.css` (or create new section)

```css
/* Task Complete Button */
.task-complete-btn {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 16px;
    border-radius: 50%;
    transition: all 0.2s ease;
    flex-shrink: 0;
}

.task-complete-btn:hover {
    transform: scale(1.1);
    background-color: #e5e7eb;
}

.task-complete-btn:active {
    transform: scale(0.95);
}

/* Completed Task State */
.task-item.completed,
.node-task-item.completed {
    opacity: 0.7;
    background-color: #f0fdf4;
    border-left: 3px solid #10b981;
}

.task-item.completed .task-title,
.node-task-item.completed .task-title {
    text-decoration: line-through;
    color: #6b7280;
}

.task-item.completed .task-complete-btn,
.node-task-item.completed .task-complete-btn {
    cursor: default;
}

.task-item.completed .task-complete-btn:hover,
.node-task-item.completed .task-complete-btn:hover {
    transform: none;
    background-color: transparent;
}
```

## Files to Modify

1. **`gtasks_dashboard/routes/api.py`** - Add complete task endpoint
2. **`gtasks_dashboard/services/data_manager.py`** - Add complete_task method
3. **`gtasks_dashboard/static/js/dashboard.js`** - Add completeTask function and update rendering
4. **`gtasks_dashboard/static/js/hierarchy-task-panel.js`** - Update task rendering with checkbox
5. **`gtasks_dashboard/static/css/components.css`** - Add complete button styles

## API Flow

1. User clicks checkbox (⭕) on incomplete task
2. `completeTask()` is called with task ID
3. POST request to `/api/tasks/{task_id}/complete`
4. Backend updates task status to 'completed' and sets completed_at
5. Backend syncs to Google Tasks (via gtasks CLI integration)
6. Frontend receives success response
7. UI updates to show ✅ and completed styling
8. Dashboard stats are refreshed

## Considerations

- **Sync to Remote**: The implementation should use the existing gtasks CLI sync mechanism to update Google Tasks
- **Error Handling**: Show error notification if sync fails
- **Optimistic UI**: Update UI immediately, revert if API fails
- **Multiple Accounts**: Support completing tasks from any account
- **Refresh After Complete**: Refresh data to update stats and other views
