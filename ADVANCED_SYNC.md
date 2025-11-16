# Advanced Sync Feature

## Overview

The Advanced Sync feature implements a 4-step simplified synchronization approach that significantly reduces the number of API calls and improves overall efficiency when synchronizing tasks between local storage and Google Tasks.

## The 4-Step Simplified Approach

### Step 1: Pull Remote Records Once
Instead of making multiple API calls, we load all remote tasks into memory once at the beginning of the process:

```python
def _load_all_google_tasks_once(self) -> List[Task]:
    # Get all tasklists
    tasklists = self.google_client.list_tasklists()
    
    # Collect all tasks from all tasklists in one go
    all_tasks = []
    for tasklist in tasklists:
        tasks = self.google_client.list_tasks(
            tasklist_id=tasklist['id'],
            show_completed=True,
            show_hidden=True,
            show_deleted=False
        )
        # Add tasklist information to each task
        for task in tasks:
            task.tasklist_id = tasklist['id']
        all_tasks.extend(tasks)
    
    return all_tasks
```

### Step 2: Compare Records Based on Latest Changes
We perform all comparisons using the local data we've already loaded:

```python
def _compare_and_plan_changes(self, local_tasks: List[Task], google_tasks: List[Task]) -> Dict:
    # Create mappings for easier lookup
    local_task_dict = {task.id: task for task in local_tasks}
    google_task_dict = {task.id: task for task in google_tasks}
    
    # Compare tasks by ID and modification time
    # Plan all changes in memory without additional API calls
```

### Step 3: Identify and Mark Duplicates
Duplicate detection is performed once on the local data:

```python
def _identify_and_mark_duplicates(self, sync_plan: Dict, local_tasks: List[Task], google_tasks: List[Task]):
    # Find duplicates in local tasks
    local_signature_map = self._create_signature_map(local_tasks)
    for signature, tasks in local_signature_map.items():
        if len(tasks) > 1:
            # Mark duplicates for removal
```

### Step 4: Execute All Changes in Batch
All changes are executed in batch operations:

```python
def _execute_sync_plan(self, sync_plan: Dict, push_only: bool, pull_only: bool) -> bool:
    # Handle push operations (if not pull_only)
    if not pull_only:
        push_success = self._execute_push_operations(sync_plan)
    
    # Handle pull operations (if not push_only)
    if not push_only:
        pull_success = self._execute_pull_operations(sync_plan)
```

## Benefits of This Approach

### 1. Reduced API Calls
- **Before**: Multiple API calls throughout the sync process
- **After**: Only one initial API call to load all remote tasks

### 2. Improved Performance
- All comparisons and decisions are made using local data
- Eliminates network latency from the decision-making process
- Reduces overall sync time

### 3. Better Resource Usage
- Fewer network requests mean less bandwidth usage
- Lower chance of hitting rate limits
- Reduced battery usage on mobile devices

### 4. Simplified Logic
- The sync process becomes more predictable
- Easier to debug and maintain
- Clear separation of concerns

## Usage

The advanced sync feature can be accessed through the CLI using the `advanced-sync` command:

```bash
# Bidirectional sync (default)
gtasks advanced-sync

# Push only
gtasks advanced-sync --push

# Pull only
gtasks advanced-sync --pull

# Specify account
gtasks advanced-sync --account myaccount
```

## Implementation Details

### Class Structure
The new implementation is contained in the `AdvancedSyncManager` class with the following key methods:

1. `sync()` - Main synchronization method that orchestrates the 4 steps
2. `_load_all_google_tasks_once()` - Loads all remote tasks in one operation
3. `_compare_and_plan_changes()` - Compares local and remote tasks
4. `_identify_and_mark_duplicates()` - Identifies duplicate tasks
5. `_execute_sync_plan()` - Executes all changes in batch

### Error Handling
The implementation includes robust error handling:
- Authentication failures are detected early
- Network errors are handled gracefully
- Partial failures don't stop the entire sync process

### Logging
Comprehensive logging helps with debugging:
- Step-by-step progress reporting
- Detailed information about decisions made
- Error conditions are clearly logged

## Future Improvements

1. **Incremental Sync**: Implement true incremental sync based on modification timestamps
2. **Parallel Processing**: Use threading to process multiple tasklists in parallel
3. **Caching**: Implement caching to avoid reloading unchanged data
4. **Conflict Resolution**: Improve conflict resolution for edge cases
5. **Progress Reporting**: Add detailed progress reporting for large sync operations