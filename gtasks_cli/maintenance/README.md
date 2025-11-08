# Maintenance Scripts

This directory contains scripts for maintaining and managing your Google Tasks.

## Deduplication Script

The [deduplicate.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/maintenance/deduplicate.py) script identifies and removes duplicate tasks from all your Google Task lists.

### Usage

```bash
# Preview what duplicates would be removed (dry-run mode)
python deduplicate.py --dry-run

# Actually remove duplicates
python deduplicate.py

# Enable verbose logging
python deduplicate.py --verbose
```

### How It Works

The script works by:

1. Connecting to your Google Tasks account
2. Retrieving all task lists
3. For each list, retrieving all tasks (including completed, hidden, and deleted tasks)
4. Creating a signature for each task based on:
   - Task title
   - Task description
   - Due date
   - Task status
5. Grouping tasks with identical signatures as duplicates
6. Keeping the most recently modified task and marking others for deletion
7. Removing the duplicate tasks

### Recommendations

1. **Run regularly**: Set up a cron job or scheduled task to run this script periodically
2. **Use dry-run first**: Always run with `--dry-run` first to preview changes
3. **Monitor logs**: Check the logs to understand what duplicates are being found and removed

### Troubleshooting

If you consistently find the same duplicates being recreated:

1. Check if there are other applications or scripts creating these tasks
2. Verify if there are sync issues with other Google Task clients
3. Consider if the tasks are being recreated by recurring task rules