# Auto-Save Feature

The auto-save feature allows you to automatically synchronize your local task changes with Google Tasks immediately after each operation (add, update, delete), without needing to run `gtasks advanced-sync` separately.

## Configuration

### Enable/Disable Auto-Save Globally

You can set auto-save in your configuration file to enable it for all commands:

```bash
# Enable auto-save
gtasks config set sync.auto_save true

# Disable auto-save
gtasks config set sync.auto_save false

# Check current setting
gtasks config get sync.auto_save
```

### Override Auto-Save Per-Command

You can override the global configuration on a per-command basis using CLI flags:

```bash
# Force auto-save for this command (even if config is false)
gtasks --auto-save add "New task"

# Disable auto-save for this command (even if config is true)
gtasks --no-auto-save add "New task"

# Use the config setting (default)
gtasks add "New task"
```

## How It Works

When auto-save is enabled:

1. **Add Command**: After creating a task locally, it's immediately pushed to Google Tasks
2. **Update Command**: After updating a task locally, the changes are immediately synced to Google Tasks
3. **Delete Command**: After deleting a task locally, it's immediately deleted from Google Tasks

### Sync Metadata Management

The auto-save feature is fully integrated with `gtasks advanced-sync`:

- Each auto-saved operation updates the sync metadata (version hashes, timestamps)
- Running `gtasks advanced-sync` later will recognize auto-saved tasks and **won't duplicate** them
- The sync system tracks which tasks have been synchronized to prevent conflicts

## Usage Examples

### Example 1: Enable Auto-Save Globally

```bash
# Enable auto-save in config
gtasks config set sync.auto_save true

# Now all operations auto-sync
gtasks add "Buy groceries"
# Output: ✅ Task added successfully: Buy groceries
#         Auto-saving to Google Tasks...
#         ✅ Auto-saved to Google Tasks

gtasks update task-id --title "Buy groceries and milk"
# Output: ✅ Task task-id updated successfully!
#         Auto-saving to Google Tasks...
#         ✅ Auto-saved to Google Tasks
```

### Example 2: Use CLI Override

```bash
# Config is set to false, but override for this command
gtasks --auto-save add "Important meeting"
# Auto-saves immediately

# Config is set to true, but disable for this command
gtasks --no-auto-save add "Draft task"
# Saves locally only
```

### Example 3: Interactive Mode

```bash
# Start interactive mode with auto-save enabled
gtasks --auto-save interactive

# All operations in interactive mode will auto-save
> add
Task title: Team standup
Task description: Daily meeting
Task 'Team standup' added successfully.
Auto-saving to Google Tasks...
✅ Auto-saved to Google Tasks
```

## Benefits

1. **Immediate Sync**: Changes appear in Google Tasks instantly
2. **No Manual Sync**: No need to remember to run `gtasks advanced-sync`
3. **Flexibility**: Can be enabled globally or per-command
4. **Compatibility**: Works seamlessly with `gtasks advanced-sync` - no duplicates
5. **Works in Interactive Mode**: Also supported in `gtasks interactive`

## Technical Details

### Task ID Management

When creating a new task with auto-save:
- Task is created locally with a UUID
- Task is pushed to Google Tasks and receives a Google Task ID
- Local storage is updated to use the Google Task ID
- Sync metadata is updated with the new ID

This ensures that:
- Local and remote tasks stay in sync
- Future syncs recognize the task as already synchronized
- No duplicate tasks are created

### Sync Metadata

Auto-save updates the following metadata:
- `local_task_versions`: Version hash of the local task
- `google_task_versions`: Version hash of the Google task
- `last_sync`: Timestamp of the last sync operation

This metadata ensures that `gtasks advanced-sync` will:
- Skip already-synced tasks
- Only sync tasks that have been modified since last sync
- Prevent duplicate operations

## Limitations

- Auto-save only works in **local mode** (not when using `--google` flag)
- Requires internet connection for each operation
- Individual task operations may be slightly slower due to immediate sync
- If Google Tasks API is unavailable, the operation will still succeed locally but auto-save will fail

## Troubleshooting

### Auto-Save Not Working

Check if auto-save is enabled:
```bash
gtasks config get sync.auto_save
```

Make sure you're not using the `--google` flag:
```bash
# This won't auto-save (already using Google Tasks directly)
gtasks --google add "Task"

# This will auto-save (if enabled)
gtasks add "Task"
```

### Tasks Being Duplicated

If you see duplicate tasks, ensure you're running the latest version of the CLI. The auto-save feature properly manages sync metadata to prevent duplicates.

### Auto-Save Failed

If auto-save fails:
- Check your internet connection
- Verify Google Tasks authentication with `gtasks auth`
- The task will still be saved locally
- You can manually sync later with `gtasks advanced-sync`
