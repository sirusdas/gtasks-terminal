# Google Tasks Recovery Guide

## Current Situation

Based on the sync log, many tasks were deleted during the duplicate removal process. Unfortunately, once tasks are deleted from Google Tasks through the API, they are not easily recoverable.

## What Was Deleted

The sync process removed tasks based on a "signature" that includes:
- Task title
- Task description
- Due date
- Status

Tasks with identical signatures were considered duplicates, and all but the most recently modified one were deleted.

## Recovery Options

### 1. Check Google Tasks Web Interface
- Visit [Google Tasks](https://tasks.google.com/)
- Check if there's any way to restore deleted tasks in the web interface
- Sometimes recently deleted tasks can be recovered through the web UI

### 2. Restore from Backup (Recommended)
You now have a backup of your current tasks:
- File: `google_tasks_backup_20251106_063835.json`
- Contains 397 tasks across 6 task lists

To restore from this backup:
```bash
python restore_tasks.py google_tasks_backup_20251106_063835.json
```

Note: The restore script will attempt to recreate tasks but cannot recreate task lists (Google Tasks API limitation).

### 3. Manual Recreation
For critical tasks that were deleted, you can manually recreate them:
```bash
# Using the gtasks CLI
python -m gtasks_cli.main add -t "Task Title" --due "2025-12-31" --priority high

# Or through the Google Tasks web interface
```

## Prevention for Future

### Always Backup Before Sync
```bash
python backup_tasks.py
```

### Use Dry-Run Mode
Always preview changes before applying them with the `--dry-run` option:
```bash
# Preview standard sync operations
gtasks sync --dry-run

# Preview batch sync operations
gtasks sync --batch --dry-run
```

### Use Safe Sync Script
We've created a safe sync script that automatically performs a dry-run first and asks for confirmation:
```bash
python gtasks_cli/safe_sync.py --batch
```

### Check Deletion Log
The system now keeps a log of all deleted tasks. You can view this log with:
```bash
gtasks deletion-log
```

This will show you all tasks that have been deleted and the reason for their deletion.

### Careful Duplicate Detection
The current duplicate detection algorithm is:
1. More accurate than the previous title-only method
2. Still may occasionally flag unique tasks as duplicates if they have very similar properties

## Scripts Available

1. **Backup Script**: `backup_tasks.py` - Creates a JSON backup of all tasks
2. **Restore Script**: `restore_tasks.py` - Restores tasks from a backup
3. **Analysis Script**: `analyze_deleted_tasks.py` - Helps identify potential issues in deletion logs
4. **Deletion Log Viewer**: Built into the CLI as `gtasks deletion-log`
5. **Safe Sync Script**: `safe_sync.py` - Performs sync with confirmation prompts

## Next Steps

1. Review the backup file to ensure it contains all your important tasks
2. If you need to recreate specific deleted tasks, use the manual creation method
3. For a full restore, use the restore script but be aware it cannot recreate task lists
4. In the future, always run backup before sync operations
5. Check the deletion log after sync operations to see what was removed
6. Use dry-run mode or the safe sync script to preview changes before applying them