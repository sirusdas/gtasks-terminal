# Advanced Sync Feature

## Overview

The Advanced Sync feature implements a 4-step simplified synchronization approach that significantly reduces the number of API calls and improves overall efficiency when synchronizing tasks between local storage and Google Tasks.

## Optimization

The Advanced Sync has been further optimized to improve performance based on the state of the local database:

1. **Full Sync for Empty Databases**: When the local database is empty, all remote tasks are pulled and stored directly without complex processing.
2. **Incremental Sync for Existing Databases**: When the local database contains data, only tasks from a specified time range are pulled to reduce data transfer and processing time.
3. **API Call Reduction**: Using combined filters in single API calls instead of multiple separate calls.

See [Advanced Sync Optimization](./ADVANCED_SYNC_OPTIMIZATION.md) for detailed information about these optimizations.

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
```

### Step 4: Execute All Changes
All changes are executed in batches to minimize API calls:

```python
def _execute_sync_plan(self, sync_plan: Dict, push_only: bool, pull_only: bool) -> bool:
    # Handle push operations (if not pull_only)
    if not pull_only:
        push_success = self._execute_push_operations(sync_plan)
    
    # Handle pull operations (if not push_only)
    if not push_only:
        pull_success = self._execute_pull_operations(sync_plan)
```

## API Call Optimization

Previously, for each task list, the system made 3 separate API calls:
1. One for completed tasks within the time range
2. One for due tasks within the time range
3. One for updated tasks within the time range

This has been optimized to make a single API call per task list with all three filters:
- `completedMin`, `dueMin`, and `updatedMin` are all specified in one request
- This returns tasks that match any of the criteria
- Results are deduplicated to avoid processing the same task multiple times

This optimization reduces the number of API calls by approximately 66%, significantly improving sync performance.

## Benefits

1. **Reduced API Calls**: The 4-step approach minimizes the number of calls to the Google Tasks API
2. **Improved Performance**: Loading data once and processing in memory is much faster
3. **Better Error Handling**: Centralized data loading makes error handling more straightforward
4. **Enhanced Reliability**: Fewer API calls mean fewer opportunities for connection issues
5. **Better API Quota Usage**: Reduced API calls help stay within Google Tasks API quotas

## Configuration

The sync behavior can be configured using the `sync.pull_range_days` setting in the configuration file:

```yaml
sync:
  pull_range_days: 90  # Default is 90 days (3 months)
```

This setting controls how far back in time to fetch tasks during incremental sync operations.

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