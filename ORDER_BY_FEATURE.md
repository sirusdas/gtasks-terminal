# Order By Feature

This document describes the new `--order-by` feature that allows users to sort tasks by different fields.

## Overview

The `--order-by` option enables users to sort their tasks by various fields including due date, creation date, modification date, priority, and title. This feature is available in both the regular `gtasks list` command and the interactive mode.

## Available Sort Options

The following sort options are available with the `--order-by` flag:

1. `due` - Sort by due date (tasks without due dates appear at the end)
2. `created` - Sort by creation date
3. `modified` - Sort by last modification date
4. `priority` - Sort by priority (critical, high, medium, low)
5. `title` - Sort by title alphabetically

## Usage Examples

### Regular Command Line Usage

```bash
# Sort tasks by due date
gtasks list --order-by due

# Sort tasks by title
gtasks list --order-by title

# Sort tasks by priority
gtasks list --order-by priority

# Combine with other filters
gtasks list "My Tasks" --status pending --order-by due

# Sort tasks by creation date
gtasks list --order-by created
```

### Interactive Mode Usage

```bash
# Start interactive mode with pre-sorted tasks
gtasks interactive -- list --order-by due

# Use within interactive mode
list --order-by title
list "Work" --order-by priority
```

## Implementation Details

The sorting functionality is implemented in the `_sort_tasks` function in [list.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/commands/list.py). The function handles special cases for different data types:

- Due date sorting places tasks without due dates at the end
- Priority sorting follows the order: critical, high, medium, low
- Date-based sorting handles None values appropriately
- Title sorting is case-insensitive

## Integration Points

1. **Command Line Interface**: The `--order-by` option is added to the `list` command using Click's option decorator
2. **Interactive Mode**: The option is parsed in both initial commands and during interactive session
3. **Initial Commands Handler**: Supports the `--order-by` option for pre-sorted initial views

## Best Practices

1. Use `due` sorting to focus on upcoming deadlines
2. Use `created` sorting to see recently added tasks
3. Use `modified` sorting to see recently updated tasks
4. Use `priority` sorting to focus on high-priority items
5. Use `title` sorting for alphabetical organization

## Examples

1. View all tasks sorted by due date:
   ```bash
   gtasks list --order-by due
   ```

2. View high-priority tasks sorted by priority level:
   ```bash
   gtasks list --priority high --order-by priority
   ```

3. View tasks in alphabetical order:
   ```bash
   gtasks list --order-by title
   ```

4. In interactive mode, start with tasks sorted by modification date:
   ```bash
   gtasks interactive -- list --order-by modified
   ```

This feature enhances the usability of the GTasks CLI by allowing users to organize their tasks in the most meaningful way for their current context.